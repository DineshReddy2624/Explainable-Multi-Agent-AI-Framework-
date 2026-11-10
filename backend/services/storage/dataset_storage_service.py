import os
import io
import json
import datetime
import pandas as pd

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal
from models.dataset import Dataset
from models.dataset_metadata import DatasetMetadata
from models.dataset_version import DatasetVersion
from models.issue import Issue
from models.anomaly import Anomaly
from models.correction import Correction
from models.report import Report
from core.tenant_security import log_audit_event
from services.agents.dynamic_analyzer import DynamicDatasetAnalyzer
from services.data_engine import data_engine
from core.file_security import validate_uploaded_file, sanitize_filename
from services.privacy.pii_detector import pii_detector
from services.privacy.pii_masker import pii_masker

active_datasets_cache: Dict[int, Dict[str, Any]] = {}

class DatasetStorageService:
    def __init__(self, upload_dir: str = settings.UPLOAD_DIR, cleaned_dir: str = settings.CLEANED_DIR):
        self.upload_dir = os.path.abspath(upload_dir)
        self.cleaned_dir = os.path.abspath(cleaned_dir)
        self.analyzer = DynamicDatasetAnalyzer()
        
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.cleaned_dir, exist_ok=True)

    def _parse_bytes_to_dataframe(self, filename: str, content: bytes) -> pd.DataFrame:
        file_bytes = io.BytesIO(content)
        lower_fn = filename.lower()

        # Check for Parquet extension or magic header bytes (PAR1)
        if lower_fn.endswith(".parquet") or content.startswith(b"PAR1"):
            try:
                return pd.read_parquet(file_bytes)
            except Exception:
                file_bytes.seek(0)
                try:
                    import pyarrow.parquet as pq
                    table = pq.read_table(file_bytes)
                    return table.to_pandas()
                except Exception:
                    file_bytes.seek(0)

        if lower_fn.endswith((".xlsx", ".xls")) or content.startswith(b"PK\x03\x04"):
            try:
                return pd.read_excel(file_bytes)
            except Exception:
                file_bytes.seek(0)
                return pd.read_csv(file_bytes)
        elif lower_fn.endswith(".json"):
            try:
                return pd.read_json(file_bytes)
            except Exception:
                file_bytes.seek(0)

        try:
            return pd.read_csv(file_bytes)
        except Exception:
            file_bytes.seek(0)
            return pd.read_excel(file_bytes)

    def save_dataset(self, filename: str, content: bytes, db: Optional[Session] = None, org_id: str = "org_default", owner_user_id: Optional[int] = None) -> Dict[str, Any]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            # 0. File Security Validation (path traversal & extension checks)
            clean_filename = validate_uploaded_file(filename, content)
            df = self._parse_bytes_to_dataframe(clean_filename, content)
            df.columns = [str(c).strip() for c in df.columns]

            # Classify source_type (DEMO vs USER_UPLOAD)
            fn_lower = clean_filename.lower()
            demo_keywords = [
                "dataset_1", "dataset_2", "dataset_3", "dataset_4", "dataset_5",
                "dataset_6", "dataset_7", "dataset_8", "dataset_9", "dataset_10",
                "customer_demographics", "e_commerce_transactions", "healthcare_patient",
                "financial_loan", "hr_employee", "iot_sensor", "customer_churn",
                "real_estate", "cybersecurity_audit", "credit_card_fraud",
                "synthetic_employees", "customer_pii", "test_task"
            ]
            is_demo = any(k in fn_lower for k in demo_keywords)
            source_type = "DEMO" if is_demo else "USER_UPLOAD"
            
            # 1. Create DB record for dataset with org_id and owner_user_id
            db_dataset = Dataset(
                org_id=org_id,
                owner_user_id=owner_user_id,
                filename=clean_filename,
                file_path="",  # Updated after ID generation
                file_size=float(len(content)),
                file_type=clean_filename.rsplit('.', 1)[-1].lower(),
                status="PROFILED",
                version_number=1,
                version_type="ORIGINAL",
                source_type=source_type,
                artifact_type="RAW_DATASET",
                is_persisted=False
            )
            db.add(db_dataset)
            db.commit()
            db.refresh(db_dataset)

            dataset_id = db_dataset.id

            # 2. Storage isolation: Create organization-scoped directory
            tenant_upload_dir = os.path.join(self.upload_dir, "organizations", org_id)
            os.makedirs(tenant_upload_dir, exist_ok=True)

            safe_disk_filename = sanitize_filename(f"dataset_{dataset_id}_{clean_filename}")
            parquet_path = os.path.join(tenant_upload_dir, f"dataset_{dataset_id}.parquet")
            raw_path = os.path.join(tenant_upload_dir, safe_disk_filename)
            
            try:
                df.to_parquet(parquet_path, index=False)
            except Exception:
                df.to_csv(parquet_path.replace(".parquet", ".csv"), index=False)

            with open(raw_path, "wb") as f:
                f.write(content)

            db_dataset.file_path = parquet_path if os.path.exists(parquet_path) else raw_path
            db.commit()

            # Create initial DatasetVersion record
            from models.dataset_version import DatasetVersion
            from core.tenant_security import log_audit_event

            initial_version = DatasetVersion(
                dataset_id=dataset_id,
                org_id=org_id,
                version_number=1,
                version_type="ORIGINAL",
                file_path=db_dataset.file_path,
                file_size=float(len(content)),
                created_by_user_id=owner_user_id
            )
            db.add(initial_version)
            db.commit()

            # 3. Analyze dataset and perform PII detection
            if os.path.exists(parquet_path):
                # DuckDB gives fast stats / missing / duplicates
                duckdb_result = data_engine.profile_dataset_duckdb(parquet_path, clean_filename)
                # DynamicDatasetAnalyzer gives format_issues, anomalies, SHAP features
                deep_result = self.analyzer.analyze(df, clean_filename)
                # Merge: use DuckDB base, overlay deep analysis fields
                analysis_result = {**duckdb_result, **{
                    "format_issues": deep_result.get("format_issues", []),
                    "anomalies": deep_result.get("anomalies", []),
                    "shap_features": deep_result.get("shap_features", []),
                    "duplicate_row_indices": deep_result.get("duplicate_row_indices", []),
                    "column_duplicates": deep_result.get("column_duplicates", []),
                    "adaptive_analysis": deep_result.get("adaptive_analysis", {}),
                    "quality_scores": deep_result.get("quality_scores", duckdb_result.get("quality_scores", {})),
                    "missing_report": deep_result.get("missing_report", duckdb_result.get("missing_report", [])),
                    "total_missing_cells": deep_result.get("total_missing_cells", duckdb_result.get("total_missing_cells", 0)),
                    "duplicate_count": deep_result.get("duplicate_count", duckdb_result.get("duplicate_count", 0)),
                }}
            else:
                analysis_result = self.analyzer.analyze(df, clean_filename)

            pii_detected = pii_detector.detect_pii_columns(df)
            analysis_result["pii_detected"] = pii_detected

            if pii_detected:
                log_audit_event("PII_DETECTED", org_id=org_id, user_id=owner_user_id, dataset_id=dataset_id, details={"pii_columns": [p["column"] for p in pii_detected]}, db=db)

            # 4. Save metadata record in DB
            db_metadata = DatasetMetadata(
                dataset_id=dataset_id,
                org_id=org_id,
                total_rows=int(analysis_result.get("total_rows", len(df))),
                total_columns=int(analysis_result.get("total_cols", len(df.columns))),
                column_names=analysis_result.get("headers", list(df.columns)),
                datatype_map={c: str(dt) for c, dt in df.dtypes.items()},
                stats_summary=analysis_result
            )
            db.add(db_metadata)
            db.commit()

            log_audit_event("DATASET_UPLOADED", org_id=org_id, user_id=owner_user_id, dataset_id=dataset_id, details={"filename": clean_filename}, db=db)

            raw_records = df.head(100).to_dict(orient="records")

            cache_payload = {
                "dataset_id": dataset_id,
                "org_id": org_id,
                "owner_user_id": owner_user_id,
                "filename": clean_filename,
                "raw_df": df,
                "cleaned_df": df.copy(),
                "analysis": analysis_result,
                "pii_detected": pii_detected,
                "records": raw_records,
                "file_path": db_dataset.file_path,
                "cleaned_file_path": None
            }

            active_datasets_cache[dataset_id] = cache_payload
            return cache_payload

        finally:
            if close_db:
                db.close()

    def load_dataset(self, dataset_id: int, db: Optional[Session] = None, org_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load a dataset from cache or persistent storage, restoring workflow bundle if available."""
        # 1. Check in-memory cache if org_id matches
        if dataset_id in active_datasets_cache:
            cached = active_datasets_cache[dataset_id]
            if org_id is None or cached.get("org_id") == org_id:
                return cached

        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            # 2. Query persistent database with tenant filter if provided
            query = db.query(Dataset).filter(Dataset.id == dataset_id)
            if org_id:
                query = query.filter(Dataset.org_id == org_id)

            db_dataset = query.first()
            if not db_dataset:
                return None

            db_metadata = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == dataset_id).first()

            # 3. Restore from workflow_bundle if it exists (full state from previous Save)
            bundle = db_metadata.workflow_bundle if db_metadata else None
            if bundle and bundle.get("final_records"):
                # We have a fully persisted workflow bundle — restore everything from DB
                final_df = pd.DataFrame(bundle["final_records"])
                final_df.columns = [str(c).strip() for c in final_df.columns]

                raw_records_preview = (
                    final_df.head(100).to_dict(orient="records")
                )

                analysis_result = bundle.get("after_analysis") or (db_metadata.stats_summary if db_metadata else {})

                cache_payload = {
                    "dataset_id": dataset_id,
                    "org_id": db_dataset.org_id,
                    "filename": db_dataset.filename,
                    "raw_df": final_df,
                    "cleaned_df": final_df.copy(),
                    "analysis": analysis_result,
                    "records": raw_records_preview,
                    "file_path": db_dataset.file_path,
                    "cleaned_file_path": db_dataset.cleaned_file_path,
                    # Restored workflow state
                    "logs": bundle.get("applied_logs", []),
                    "workflow_bundle": bundle,
                }

                active_datasets_cache[dataset_id] = cache_payload
                return cache_payload

            # 4. No bundle — load Parquet / CSV file from persistent storage disk
            db_org_id = db_dataset.org_id or org_id or "org_default"
            tenant_cleaned_dir = os.path.join(self.cleaned_dir, "organizations", db_org_id)
            tenant_upload_dir = os.path.join(self.upload_dir, "organizations", db_org_id)

            possible_paths = [
                db_dataset.cleaned_file_path if db_dataset.cleaned_file_path else "",
                os.path.join(tenant_cleaned_dir, f"cleaned_dataset_{dataset_id}.parquet"),
                os.path.join(tenant_cleaned_dir, f"cleaned_dataset_{dataset_id}.csv"),
                db_dataset.file_path if db_dataset.file_path else "",
                os.path.join(tenant_upload_dir, f"dataset_{dataset_id}.parquet"),
                os.path.join(self.cleaned_dir, f"cleaned_dataset_{dataset_id}.parquet"),
                os.path.join(self.cleaned_dir, f"cleaned_dataset_{dataset_id}.csv"),
                os.path.join(self.upload_dir, f"dataset_{dataset_id}.parquet")
            ]

            df = None
            for p in possible_paths:
                if p and os.path.exists(p):
                    try:
                        if p.endswith(".parquet"):
                            df = pd.read_parquet(p)
                        elif p.endswith((".xlsx", ".xls")):
                            df = pd.read_excel(p)
                        else:
                            df = pd.read_csv(p)
                        if df is not None and not df.empty:
                            break
                    except Exception:
                        continue

            if df is None:
                return None

            df.columns = [str(c).strip() for c in df.columns]

            analysis_result = db_metadata.stats_summary if (db_metadata and db_metadata.stats_summary) else self.analyzer.analyze(df, db_dataset.filename)
            raw_records = df.head(100).to_dict(orient="records")

            cache_payload = {
                "dataset_id": dataset_id,
                "org_id": db_dataset.org_id,
                "filename": db_dataset.filename,
                "raw_df": df,
                "cleaned_df": df.copy(),
                "analysis": analysis_result,
                "records": raw_records,
                "file_path": db_dataset.file_path,
                "cleaned_file_path": db_dataset.cleaned_file_path,
                "logs": [],
                "workflow_bundle": None
            }

            active_datasets_cache[dataset_id] = cache_payload
            return cache_payload

        finally:
            if close_db:
                db.close()

    def load_workflow_bundle(self, dataset_id: int, db: Optional[Session] = None, org_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Returns the complete persisted workflow state for a dataset — all 14 items
        (original records, final records, change history, quality decisions,
        anomaly decisions, before/after analysis, applied logs, metadata).

        Returns None if no workflow bundle has been saved for this dataset yet.
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            query = db.query(Dataset).filter(Dataset.id == dataset_id)
            if org_id:
                query = query.filter(Dataset.org_id == org_id)
            db_dataset = query.first()
            if not db_dataset:
                return None

            db_metadata = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == dataset_id).first()
            if not db_metadata or not db_metadata.workflow_bundle:
                return None

            bundle = db_metadata.workflow_bundle
            return {
                # ─ Core bundle ───────────────────────────────────────────────
                "dataset_id": dataset_id,
                "filename": db_dataset.filename,
                "org_id": db_dataset.org_id,
                "status": db_dataset.status,
                # ─ Dataset data (all 14 items) ─────────────────────────────
                "original_records": bundle.get("original_records", []),
                "final_records": bundle.get("final_records", []),
                "change_history": bundle.get("change_history", []),
                "quality_decisions": bundle.get("quality_decisions", {}),
                "anomaly_decisions": bundle.get("anomaly_decisions", {}),
                "applied_logs": bundle.get("applied_logs", []),
                "before_analysis": bundle.get("before_analysis", {}),
                "after_analysis": bundle.get("after_analysis", {}),
                # ─ File references ───────────────────────────────────────────
                "original_file_path": bundle.get("original_file_path"),
                "final_file_path": bundle.get("final_file_path"),
                # ─ Summary metadata ──────────────────────────────────────────
                "total_rows_original": bundle.get("total_rows_original", 0),
                "total_rows_final": bundle.get("total_rows_final", 0),
                "total_cols": bundle.get("total_cols", 0),
                "column_names": bundle.get("column_names", []),
                "saved_at": bundle.get("saved_at") or (db_metadata.saved_at.isoformat() if db_metadata.saved_at else None),
                "saved_by_user_id": bundle.get("saved_by_user_id"),
                "change_history_count": len(bundle.get("change_history", [])),
                "quality_decisions_count": len(bundle.get("quality_decisions", {})),
                "anomaly_decisions_count": len(bundle.get("anomaly_decisions", {})),
                "workflow_bundle_stored": True,
            }
        finally:
            if close_db:
                db.close()

    def save_cleaned_dataset(
        self,
        dataset_id: int,
        cleaned_df: pd.DataFrame,
        logs: List[Any],
        db: Optional[Session] = None,
        org_id: str = "org_default",
        user_id: Optional[int] = None,
        workflow_bundle: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Persists the cleaned dataset and the COMPLETE workflow bundle so that
        after any restart (browser / server / computer) the full state can be
        restored — including original records, change history, quality/anomaly
        decisions, and before/after analysis results.

        Parameters
        ----------
        workflow_bundle : dict, optional
            Keys expected:
                original_records    – list[dict] – raw rows before any editing
                change_history      – list[dict] – every cell-level change
                quality_decisions   – dict       – {"row_col_key": {...}}
                anomaly_decisions   – dict       – {"row_col_key": {...}}
                before_analysis     – dict       – profiling snapshot at upload time
                after_analysis      – dict       – profiling snapshot at save time
                applied_logs        – list[dict] – remediation log entries
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            cached = self.load_dataset(dataset_id, db=db, org_id=org_id)
            filename = cached["filename"] if cached else f"dataset_{dataset_id}.csv"

            # ── Storage isolation ────────────────────────────────────────────
            tenant_cleaned_dir = os.path.join(self.cleaned_dir, "organizations", org_id)
            tenant_upload_dir = os.path.join(self.upload_dir, "organizations", org_id)
            os.makedirs(tenant_cleaned_dir, exist_ok=True)
            os.makedirs(tenant_upload_dir, exist_ok=True)

            clean_parquet_path = os.path.join(tenant_cleaned_dir, f"cleaned_dataset_{dataset_id}.parquet")
            clean_csv_path = os.path.join(tenant_cleaned_dir, f"cleaned_dataset_{dataset_id}.csv")

            # ── Persist final (cleaned) dataset ──────────────────────────────
            try:
                cleaned_df.to_parquet(clean_parquet_path, index=False)
            except Exception:
                pass
            cleaned_df.to_csv(clean_csv_path, index=False)

            # ── Persist original dataset (immutable reference) ───────────────
            original_parquet_path = os.path.join(tenant_upload_dir, f"original_dataset_{dataset_id}.parquet")
            original_csv_path = os.path.join(tenant_upload_dir, f"original_dataset_{dataset_id}.csv")
            original_records_for_db: List[Dict] = []

            if workflow_bundle and workflow_bundle.get("original_records"):
                original_records_for_db = workflow_bundle["original_records"]
                if not os.path.exists(original_parquet_path):  # Never overwrite original
                    orig_df = pd.DataFrame(original_records_for_db)
                    try:
                        orig_df.to_parquet(original_parquet_path, index=False)
                    except Exception:
                        pass
                    orig_df.to_csv(original_csv_path, index=False)
            elif cached and cached.get("raw_df") is not None:
                # Fallback: save the cached raw_df as original if no bundle provided
                orig_df = cached["raw_df"].copy()
                if not os.path.exists(original_parquet_path):
                    try:
                        orig_df.to_parquet(original_parquet_path, index=False)
                    except Exception:
                        pass
                    orig_df.to_csv(original_csv_path, index=False)

            # ── Recalculate after-state profiling ────────────────────────────
            new_analysis = self.analyzer.analyze(cleaned_df, filename)

            # ── Build the persistent workflow bundle ──────────────────────────
            # This is the complete state that survives server/browser restarts.
            final_records_list = (
                cleaned_df.to_dict(orient="records")
                if len(cleaned_df) <= 10000
                else cleaned_df.head(10000).to_dict(orient="records")
            )

            bundle_to_store: Dict[str, Any] = {
                # ─ Dataset data ─────────────────────────────────────────────
                "original_records": original_records_for_db,          # A – Original Dataset
                "final_records": final_records_list,                   # B – Final Modified Dataset
                # ─ Workflow decisions ────────────────────────────────────────
                "change_history": (workflow_bundle or {}).get("change_history", []),     # M
                "quality_decisions": (workflow_bundle or {}).get("quality_decisions", {}),  # E, F, L
                "anomaly_decisions": (workflow_bundle or {}).get("anomaly_decisions", {}),  # G, H
                "applied_logs": (workflow_bundle or {}).get("applied_logs", logs or []),    # J, K
                # ─ Analysis results ──────────────────────────────────────────
                "before_analysis": (workflow_bundle or {}).get("before_analysis") or (cached or {}).get("analysis", {}),  # D
                "after_analysis": (workflow_bundle or {}).get("after_analysis") or new_analysis,  # D after
                # ─ File references ───────────────────────────────────────────
                "original_file_path": original_parquet_path if os.path.exists(original_parquet_path) else original_csv_path,
                "final_file_path": clean_parquet_path if os.path.exists(clean_parquet_path) else clean_csv_path,
                # ─ Metadata ──────────────────────────────────────────────────
                "dataset_id": dataset_id,
                "filename": filename,
                "org_id": org_id,
                "saved_by_user_id": user_id,
                "total_rows_original": len(original_records_for_db),
                "total_rows_final": len(cleaned_df),
                "total_cols": len(cleaned_df.columns),
                "column_names": list(cleaned_df.columns),
                "saved_at": datetime.datetime.utcnow().isoformat(),
            }

            # ── Check if this is an explicit permanent save (workflow_bundle provided) ──
            is_explicit_save = bool(
                workflow_bundle is not None and (
                    workflow_bundle.get("original_records") or
                    workflow_bundle.get("change_history") or
                    workflow_bundle.get("records") or
                    workflow_bundle.get("quality_decisions") or
                    workflow_bundle.get("anomaly_decisions")
                )
            )

            # ── Update Dataset record ────────────────────────────────────────
            db_dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.org_id == org_id).first()
            new_version_num = 2
            clean_filename_base = os.path.basename(clean_csv_path)

            if db_dataset:
                db_dataset.cleaned_file_path = clean_csv_path
                db_dataset.version_number = (db_dataset.version_number or 1) + 1
                db_dataset.cleaned_filename = clean_filename_base

                if is_explicit_save:
                    db_dataset.status = "SAVED"
                    db_dataset.version_type = "SAVED"
                    db_dataset.is_persisted = True
                    db_dataset.artifact_type = "CLEANED_DATASET"
                    db_dataset.source_type = "CLEANED_DATASET"
                else:
                    # Intermediate remediation step (preview/working version)
                    db_dataset.status = "CLEANED"
                    db_dataset.version_type = "CLEANED"
                    db_dataset.is_persisted = False
                    db_dataset.artifact_type = "RAW_DATASET"

                new_version_num = db_dataset.version_number
                db.commit()

            # ── Record version lineage ────────────────────────────────────────
            from models.dataset_version import DatasetVersion
            from core.tenant_security import log_audit_event

            new_version = DatasetVersion(
                dataset_id=dataset_id,
                org_id=org_id,
                version_number=new_version_num,
                parent_version_id=1,
                version_type="SAVED" if is_explicit_save else "CLEANED",
                file_path=clean_csv_path,
                file_size=float(os.path.getsize(clean_csv_path)) if os.path.exists(clean_csv_path) else 0.0,
                created_by_user_id=user_id
            )
            db.add(new_version)

            # ── Persist full workflow bundle into DatasetMetadata ─────────────
            db_metadata = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == dataset_id).first()
            if is_explicit_save:
                if db_metadata:
                    db_metadata.stats_summary = new_analysis
                    db_metadata.total_rows = len(cleaned_df)
                    db_metadata.total_columns = len(cleaned_df.columns)
                    db_metadata.column_names = list(cleaned_df.columns)
                    db_metadata.workflow_bundle = bundle_to_store  # ← PERSISTED BUNDLE
                    db_metadata.original_file_path = bundle_to_store.get("original_file_path")
                    db_metadata.saved_at = datetime.datetime.utcnow()
                    db.commit()
                else:
                    # Create metadata record if it doesn't exist
                    db_metadata = DatasetMetadata(
                        dataset_id=dataset_id,
                        org_id=org_id,
                        total_rows=len(cleaned_df),
                        total_columns=len(cleaned_df.columns),
                        column_names=list(cleaned_df.columns),
                        datatype_map={c: str(dt) for c, dt in cleaned_df.dtypes.items()},
                        stats_summary=new_analysis,
                        workflow_bundle=bundle_to_store,
                        original_file_path=bundle_to_store.get("original_file_path"),
                        saved_at=datetime.datetime.utcnow()
                    )
                    db.add(db_metadata)
                    db.commit()

                log_audit_event("DATASET_SAVED", org_id=org_id, user_id=user_id, dataset_id=dataset_id, details={"filename": filename, "rows": len(cleaned_df), "workflow_bundle_keys": list(bundle_to_store.keys())}, db=db)
            else:
                # Intermediate cleaning only updates stats, not the saved repository
                if db_metadata:
                    db_metadata.stats_summary = new_analysis
                    db_metadata.total_rows = len(cleaned_df)
                    db_metadata.total_columns = len(cleaned_df.columns)
                    db_metadata.column_names = list(cleaned_df.columns)
                    db.commit()

            # ── Update in-memory cache ────────────────────────────────────────
            new_records_preview = (
                cleaned_df.to_dict(orient="records")
                if len(cleaned_df) <= 5000
                else cleaned_df.head(1000).to_dict(orient="records")
            )

            cache_payload = {
                "dataset_id": dataset_id,
                "org_id": org_id,
                "filename": filename,
                "raw_df": cached.get("raw_df", cleaned_df) if cached else cleaned_df,
                "cleaned_df": cleaned_df,
                "analysis": new_analysis,
                "records": new_records_preview,
                "logs": bundle_to_store["applied_logs"],
                "file_path": cached.get("file_path") if cached else clean_csv_path,
                "cleaned_file_path": clean_csv_path,
                "workflow_bundle": bundle_to_store
            }

            active_datasets_cache[dataset_id] = cache_payload
            return {
                "dataset_id": dataset_id,
                "org_id": org_id,
                "saved": True,
                "success": True,
                "version_name": "SAVED",
                "version_type": "SAVED",
                "records": new_records_preview,
                "analysis": new_analysis,
                "logs": bundle_to_store["applied_logs"],
                "cleaned_file_path": clean_csv_path,
                "original_file_path": bundle_to_store.get("original_file_path"),
                "workflow_bundle_stored": True,
                "saved_at": bundle_to_store["saved_at"],
                "total_rows_original": bundle_to_store["total_rows_original"],
                "total_rows_final": bundle_to_store["total_rows_final"],
                "change_history_count": len(bundle_to_store["change_history"]),
                "quality_decisions_count": len(bundle_to_store["quality_decisions"]),
                "anomaly_decisions_count": len(bundle_to_store["anomaly_decisions"]),
            }

        finally:
            if close_db:
                db.close()

    def save_pii_masked_dataset(self, dataset_id: int, db: Optional[Session] = None, org_id: str = "org_default", user_id: Optional[int] = None) -> Dict[str, Any]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            cached = self.load_dataset(dataset_id, db=db, org_id=org_id)
            if not cached:
                raise ValueError(f"Dataset #{dataset_id} not found.")

            raw_df = cached["raw_df"].copy()
            pii_columns = cached.get("pii_detected") or pii_detector.detect_pii_columns(raw_df)

            masked_df, logs = pii_masker.mask_dataframe(raw_df, pii_columns)

            tenant_cleaned_dir = os.path.join(self.cleaned_dir, "organizations", org_id)
            os.makedirs(tenant_cleaned_dir, exist_ok=True)
            masked_csv_path = os.path.join(tenant_cleaned_dir, f"masked_dataset_{dataset_id}.csv")
            masked_df.to_csv(masked_csv_path, index=False)

            db_dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.org_id == org_id).first()
            new_version_num = (db_dataset.version_number or 1) + 1 if db_dataset else 2
            if db_dataset:
                db_dataset.status = "PII_MASKED"
                db_dataset.cleaned_file_path = masked_csv_path
                db_dataset.version_number = new_version_num
                db_dataset.version_type = "PII_MASKED"
                db.commit()

            from models.dataset_version import DatasetVersion
            from core.tenant_security import log_audit_event

            masked_version = DatasetVersion(
                dataset_id=dataset_id,
                org_id=org_id,
                version_number=new_version_num,
                parent_version_id=1,
                version_type="PII_MASKED",
                file_path=masked_csv_path,
                file_size=float(os.path.getsize(masked_csv_path)) if os.path.exists(masked_csv_path) else 0.0,
                created_by_user_id=user_id
            )
            db.add(masked_version)
            db.commit()

            log_audit_event("PII_MASKED", org_id=org_id, user_id=user_id, dataset_id=dataset_id, details={"logs": logs}, db=db)

            cached["cleaned_df"] = masked_df
            cached["cleaned_file_path"] = masked_csv_path
            active_datasets_cache[dataset_id] = cached

            return {
                "dataset_id": dataset_id,
                "org_id": org_id,
                "version_number": new_version_num,
                "logs": logs,
                "masked_file_path": masked_csv_path,
                "records": masked_df.head(100).to_dict(orient="records")
            }
        finally:
            if close_db:
                db.close()

    def list_datasets(self, db: Optional[Session] = None, org_id: Optional[str] = None, saved_only: bool = False) -> List[Dict[str, Any]]:
        """
        List datasets.
        When saved_only=True, returns strictly valid persisted cleaned datasets that satisfy:
          is_persisted = True AND artifact_type = 'CLEANED_DATASET' (with workflow_bundle)
        When saved_only=False, returns all datasets for working/preview context.
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            results = []
            query = db.query(Dataset)
            if org_id:
                query = query.filter(Dataset.org_id == org_id)

            if saved_only:
                # Strictly eligible saved repository records
                query = query.filter(
                    Dataset.is_persisted == True,
                    Dataset.artifact_type == "CLEANED_DATASET"
                )

            db_datasets = query.order_by(Dataset.id.desc()).all()

            for d in db_datasets:
                db_meta = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == d.id).first()
                analysis = db_meta.stats_summary if (db_meta and db_meta.stats_summary) else {}
                bundle = db_meta.workflow_bundle if db_meta else None

                # If saved_only is requested, ensure there is an actual persisted workflow bundle
                if saved_only and not (bundle and bundle.get("final_records")):
                    continue

                # Prefer bundle counts over metadata if bundle is present (more accurate)
                total_rows = (
                    bundle.get("total_rows_final", 0)
                    if bundle
                    else analysis.get("total_rows", 0)
                )
                total_cols = (
                    bundle.get("total_cols", 0)
                    if bundle
                    else analysis.get("total_cols", 0)
                )

                # Quality score from after_analysis if bundle available
                after_analysis = bundle.get("after_analysis", {}) if bundle else {}
                quality_score = (
                    after_analysis.get("quality_scores", {}).get("overall_score")
                    or analysis.get("quality_scores", {}).get("overall_score", 100)
                )

                saved_at = None
                if db_meta and db_meta.saved_at:
                    saved_at = db_meta.saved_at.isoformat()
                elif bundle and bundle.get("saved_at"):
                    saved_at = bundle["saved_at"]

                cleaned_fn = d.cleaned_filename or (f"cleaned_{d.filename}" if not d.filename.startswith("cleaned_") else d.filename)
                original_fn = d.filename

                saved_ts = int(db_meta.saved_at.timestamp()) if (db_meta and db_meta.saved_at) else (int(d.created_at.timestamp()) if d.created_at else d.id)
                workflow_id = f"WF-{d.id}-{saved_ts}"

                results.append({
                    "id": d.id,
                    "dataset_id": d.id,
                    "org_id": d.org_id,
                    "filename": cleaned_fn if (d.is_persisted or d.status == "SAVED") else original_fn,
                    "original_filename": original_fn,
                    "cleaned_filename": cleaned_fn,
                    "source_type": d.source_type or ("CLEANED_DATASET" if d.is_persisted else "USER_UPLOAD"),
                    "artifact_type": d.artifact_type or ("CLEANED_DATASET" if d.is_persisted else "RAW_DATASET"),
                    "total_rows": total_rows,
                    "original_row_count": bundle.get("total_rows_original", 0) if bundle else (db_meta.total_rows if db_meta else 0),
                    "final_row_count": total_rows,
                    "total_cols": total_cols,
                    "quality_score": quality_score,
                    "status": d.status,
                    "cleaning_status": d.status,
                    "is_persisted": bool(d.is_persisted),
                    "persistence_status": "Persistently Stored" if (d.is_persisted or d.status == "SAVED") else "Unsaved",
                    "workflow_id": workflow_id,
                    "storage_path": d.cleaned_file_path or d.file_path,
                    "created_by": d.owner_user_id,
                    "version_number": d.version_number,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                    "saved_at": saved_at,
                    # Persistence flags — tells frontend exactly what is stored
                    "has_workflow_bundle": bool(bundle and bundle.get("final_records")),
                    "has_original_records": bool(bundle and bundle.get("original_records")),
                    "change_events": len(bundle.get("change_history", [])) if bundle else 0,
                    "change_history_count": len(bundle.get("change_history", [])) if bundle else 0,
                    "quality_decisions_count": len(bundle.get("quality_decisions", {})) if bundle else 0,
                    "anomaly_decisions_count": len(bundle.get("anomaly_decisions", {})) if bundle else 0,
                    "total_rows_original": bundle.get("total_rows_original", 0) if bundle else 0,
                })

            return results
        finally:
            if close_db:
                db.close()

    def delete_dataset(self, dataset_id: int, db: Optional[Session] = None, org_id: str = "org_default") -> bool:
        """
        Permanently delete a dataset, its versions, metadata, associated child records,
        and underlying files from storage.
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            # 1. Fetch dataset
            query = db.query(Dataset).filter(Dataset.id == dataset_id)
            if org_id:
                query = query.filter(Dataset.org_id == org_id)
            dataset = query.first()
            if not dataset:
                return False

            effective_org_id = dataset.org_id or org_id or "org_default"

            # 2. Gather all file paths to remove from disk
            paths_to_delete = []
            if dataset.file_path:
                paths_to_delete.append(dataset.file_path)
            if dataset.cleaned_file_path:
                paths_to_delete.append(dataset.cleaned_file_path)

            from models.dataset_version import DatasetVersion
            from models.dataset_metadata import DatasetMetadata
            from models.report import Report
            from models.quality_score import QualityScore
            from models.monitor_log import MonitorLog
            from models.issue import Issue
            from models.generated_code import GeneratedCode
            from models.correction import Correction
            from models.chat_history import ChatHistory
            from models.anomaly import Anomaly

            versions = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).all()
            for v in versions:
                if v.file_path:
                    paths_to_delete.append(v.file_path)

            # Also check tenant dirs for files with this dataset_id pattern
            tenant_cleaned_dir = os.path.join(self.cleaned_dir, "organizations", effective_org_id)
            tenant_upload_dir = os.path.join(self.upload_dir, "organizations", effective_org_id)
            paths_to_delete.extend([
                os.path.join(tenant_cleaned_dir, f"cleaned_dataset_{dataset_id}.csv"),
                os.path.join(tenant_cleaned_dir, f"cleaned_dataset_{dataset_id}.parquet"),
                os.path.join(tenant_upload_dir, f"original_dataset_{dataset_id}.csv"),
                os.path.join(tenant_upload_dir, f"original_dataset_{dataset_id}.parquet"),
                os.path.join(tenant_upload_dir, f"dataset_{dataset_id}.csv"),
                os.path.join(tenant_upload_dir, f"dataset_{dataset_id}.parquet"),
            ])

            for p in set(paths_to_delete):
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception as err:
                        logger.warning(f"Could not remove disk file {p}: {err}")

            # 3. Clean up related dependent records
            models_to_clean = [
                DatasetMetadata, DatasetVersion, Report, QualityScore,
                MonitorLog, Issue, GeneratedCode, Correction, ChatHistory, Anomaly
            ]
            for model_cls in models_to_clean:
                try:
                    db.query(model_cls).filter(model_cls.dataset_id == dataset_id).delete(synchronize_session=False)
                except Exception as err:
                    logger.warning(f"Could not delete {model_cls.__name__} for dataset {dataset_id}: {err}")

            # 4. Delete the dataset record itself
            db.delete(dataset)
            db.commit()

            # 5. Remove from in-memory active datasets cache
            if dataset_id in active_datasets_cache:
                del active_datasets_cache[dataset_id]

            return True
        finally:
            if close_db:
                db.close()

storage_service = DatasetStorageService()
