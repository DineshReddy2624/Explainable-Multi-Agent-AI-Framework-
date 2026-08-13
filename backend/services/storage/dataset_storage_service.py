import os
import io
import json
import pandas as pd

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal
from models.dataset import Dataset
from models.dataset_metadata import DatasetMetadata
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

        if lower_fn.endswith((".xlsx", ".xls")):
            try:
                return pd.read_excel(file_bytes)
            except Exception:
                file_bytes.seek(0)
                return pd.read_csv(file_bytes)
        else:
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
                version_type="ORIGINAL"
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

            # 3. Load Parquet / CSV file from persistent storage disk
            cleaned_path = os.path.join(self.cleaned_dir, f"cleaned_dataset_{dataset_id}.parquet")
            cleaned_csv_path = os.path.join(self.cleaned_dir, f"cleaned_dataset_{dataset_id}.csv")
            parquet_path = os.path.join(self.upload_dir, f"dataset_{dataset_id}.parquet")

            df = None
            if os.path.exists(cleaned_path):
                try:
                    df = pd.read_parquet(cleaned_path)
                except Exception:
                    df = pd.read_csv(cleaned_csv_path) if os.path.exists(cleaned_csv_path) else None

            if df is None and os.path.exists(cleaned_csv_path):
                df = pd.read_csv(cleaned_csv_path)

            if df is None and os.path.exists(parquet_path):
                try:
                    df = pd.read_parquet(parquet_path)
                except Exception:
                    df = None

            if df is None and os.path.exists(db_dataset.file_path):
                if db_dataset.file_path.endswith(".parquet"):
                    df = pd.read_parquet(db_dataset.file_path)
                elif db_dataset.file_path.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(db_dataset.file_path)
                else:
                    df = pd.read_csv(db_dataset.file_path)

            if df is None:
                return None

            df.columns = [str(c).strip() for c in df.columns]

            analysis_result = db_metadata.stats_summary if (db_metadata and db_metadata.stats_summary) else self.analyzer.analyze(df, db_dataset.filename)
            raw_records = df.head(100).to_dict(orient="records")

            cache_payload = {
                "dataset_id": dataset_id,
                "filename": db_dataset.filename,
                "raw_df": df,
                "cleaned_df": df.copy(),
                "analysis": analysis_result,
                "records": raw_records,
                "file_path": db_dataset.file_path,
                "cleaned_file_path": db_dataset.cleaned_file_path
            }

            active_datasets_cache[dataset_id] = cache_payload
            return cache_payload

        finally:
            if close_db:
                db.close()

    def save_cleaned_dataset(self, dataset_id: int, cleaned_df: pd.DataFrame, logs: List[Any], db: Optional[Session] = None, org_id: str = "org_default", user_id: Optional[int] = None) -> Dict[str, Any]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            cached = self.load_dataset(dataset_id, db=db, org_id=org_id)
            filename = cached["filename"] if cached else f"dataset_{dataset_id}.csv"

            # Storage isolation for cleaned dataset
            tenant_cleaned_dir = os.path.join(self.cleaned_dir, "organizations", org_id)
            os.makedirs(tenant_cleaned_dir, exist_ok=True)

            clean_parquet_path = os.path.join(tenant_cleaned_dir, f"cleaned_dataset_{dataset_id}.parquet")
            clean_csv_path = os.path.join(tenant_cleaned_dir, f"cleaned_dataset_{dataset_id}.csv")

            try:
                cleaned_df.to_parquet(clean_parquet_path, index=False)
            except Exception:
                pass
            cleaned_df.to_csv(clean_csv_path, index=False)

            # Recalculate profiling stats
            new_analysis = self.analyzer.analyze(cleaned_df, filename)

            # Update Database record
            db_dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.org_id == org_id).first()
            new_version_num = 2
            if db_dataset:
                db_dataset.status = "CLEANED"
                db_dataset.cleaned_file_path = clean_csv_path
                db_dataset.version_number = (db_dataset.version_number or 1) + 1
                db_dataset.version_type = "CLEANED"
                new_version_num = db_dataset.version_number
                db.commit()

            # Record version lineage
            from models.dataset_version import DatasetVersion
            from core.tenant_security import log_audit_event

            new_version = DatasetVersion(
                dataset_id=dataset_id,
                org_id=org_id,
                version_number=new_version_num,
                parent_version_id=1,
                version_type="CLEANED",
                file_path=clean_csv_path,
                file_size=float(os.path.getsize(clean_csv_path)) if os.path.exists(clean_csv_path) else 0.0,
                created_by_user_id=user_id
            )
            db.add(new_version)

            db_metadata = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == dataset_id).first()
            if db_metadata:
                db_metadata.stats_summary = new_analysis
                db_metadata.total_rows = len(cleaned_df)
                db_metadata.total_columns = len(cleaned_df.columns)
                db.commit()

            log_audit_event("DATASET_REMEDIATED", org_id=org_id, user_id=user_id, dataset_id=dataset_id, details={"logs": logs}, db=db)

            new_records = cleaned_df.head(100).to_dict(orient="records")

            cache_payload = {
                "dataset_id": dataset_id,
                "org_id": org_id,
                "filename": filename,
                "raw_df": cached.get("raw_df", cleaned_df) if cached else cleaned_df,
                "cleaned_df": cleaned_df,
                "analysis": new_analysis,
                "records": new_records,
                "file_path": cached.get("file_path") if cached else clean_csv_path,
                "cleaned_file_path": clean_csv_path
            }

            active_datasets_cache[dataset_id] = cache_payload
            return {
                "dataset_id": dataset_id,
                "org_id": org_id,
                "version_name": "CLEANED",
                "version_type": "CLEANED",
                "records": new_records,
                "analysis": new_analysis,
                "logs": logs,
                "cleaned_file_path": clean_csv_path
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

    def list_datasets(self, db: Optional[Session] = None, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            results = []
            query = db.query(Dataset)
            if org_id:
                query = query.filter(Dataset.org_id == org_id)

            db_datasets = query.order_by(Dataset.id.desc()).all()
            
            for d in db_datasets:
                db_meta = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == d.id).first()
                analysis = db_meta.stats_summary if (db_meta and db_meta.stats_summary) else {}
                
                results.append({
                    "id": d.id,
                    "dataset_id": d.id,
                    "org_id": d.org_id,
                    "filename": d.filename,
                    "total_rows": analysis.get("total_rows", 0),
                    "total_cols": analysis.get("total_cols", 0),
                    "quality_score": analysis.get("quality_scores", {}).get("overall_score", 100),
                    "status": d.status,
                    "version_number": d.version_number,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                })
                
            return results
        finally:
            if close_db:
                db.close()

storage_service = DatasetStorageService()
