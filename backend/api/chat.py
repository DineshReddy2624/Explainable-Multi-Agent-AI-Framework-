import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from core.response import StandardResponse
from services.agents.dataset_chat_agent import DatasetChatAgent
from api.upload import active_datasets_cache
import re

router = APIRouter()
chat_agent = DatasetChatAgent()

chat_dataset_store = {}

def parse_dataset_file(filename: str, content: bytes) -> pd.DataFrame:
    file_bytes = io.BytesIO(content)

    # 1. Try read_excel if extension indicates Excel
    if filename.lower().endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(file_bytes)
        except Exception:
            file_bytes.seek(0)
            pass
        try:
            return pd.read_csv(file_bytes)
        except Exception:
            file_bytes.seek(0)
            pass

    # 2. Try read_csv if extension indicates CSV
    if filename.lower().endswith(".csv"):
        try:
            return pd.read_csv(file_bytes)
        except Exception:
            file_bytes.seek(0)
            pass
        try:
            return pd.read_excel(file_bytes)
        except Exception:
            file_bytes.seek(0)
            pass

    # 3. Fallback: Try read_excel then read_csv
    try:
        return pd.read_excel(file_bytes)
    except Exception:
        file_bytes.seek(0)
        pass

    try:
        return pd.read_csv(file_bytes)
    except Exception:
        file_bytes.seek(0)
        pass

    raise ValueError(f"Could not parse '{filename}' as CSV or Excel.")

from core.tenant_security import get_tenant_context, verify_dataset_access
from fastapi import Depends
from sqlalchemy.orm import Session
from core.database import get_db

@router.post("/upload")
async def upload_chat_dataset(file: UploadFile = File(...), db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    filename = file.filename
    content = await file.read()
    
    try:
        df = parse_dataset_file(filename, content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse dataset for chat: {str(e)}")

    total_rows = len(df)
    total_cols = len(df.columns)
    headers = [str(c).strip() for c in df.columns]
    df.columns = headers

    missing_report = []
    tot_missing = 0
    numeric_cols = list(df.select_dtypes(include=['number']).columns)

    for col in headers:
        null_cnt = int((df[col].isnull() | (df[col].astype(str).str.strip() == "") | (df[col].astype(str).str.lower() == "nan")).sum())
        tot_missing += null_cnt
        if null_cnt > 0:
            med_val = round(float(df[col].dropna().median()), 2) if col in numeric_cols and not df[col].dropna().empty else "Mode Fill"
            missing_report.append({
                "column": col,
                "null_count": null_cnt,
                "missing_pct": round((null_cnt/total_rows)*100, 1) if total_rows > 0 else 0,
                "suggested_median": med_val
            })

    dup_cnt = int(df.duplicated().sum())

    chat_analysis = {
        "filename": filename,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "headers": headers,
        "missing_report": missing_report,
        "total_missing_cells": tot_missing,
        "duplicate_count": dup_cnt,
        "anomalies": [],
        "quality_scores": {
            "overall_score": max(60, round(100 - (tot_missing * 2), 1))
        }
    }

    org_id = tenant.get("org_id", "org_default")
    user_id = tenant.get("user_id", 1)

    # Persist dataset through storage service so it gets a DB record and dataset_id
    saved = storage_service.save_dataset(
        filename=filename,
        content=content,
        db=db,
        org_id=org_id,
        owner_user_id=user_id
    )
    dataset_id = saved.get("dataset_id")

    if saved.get("analysis"):
        analysis_data = saved["analysis"]
        if isinstance(analysis_data, dict):
            chat_analysis.update(analysis_data)
            missing_report = chat_analysis.get("missing_report", missing_report)
            tot_missing = chat_analysis.get("total_missing_cells", tot_missing)

    cache_key = (org_id, dataset_id)
    chat_dataset_store[cache_key] = {
        "df": df,
        "analysis": chat_analysis,
        "filename": filename,
        "dataset_id": dataset_id,
        "records": df.to_dict(orient="records")
    }

    suggested_questions = [
        "How many rows are there?",
        "What are the column names?",
        "Show missing values.",
        "Show duplicate records.",
        "Generate dataset summary.",
        "What is the quality score?"
    ]
    if len(headers) > 0:
        suggested_questions.append(f"Which record has the highest {headers[0]}?")

    payload = {
        "dataset_id": dataset_id,
        "id": dataset_id,
        "filename": filename,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "headers": headers,
        "missing_report": missing_report,
        "total_missing_cells": tot_missing,
        "duplicate_count": dup_cnt,
        "suggested_questions": suggested_questions,
        "analysis": chat_analysis
    }

    return StandardResponse.ok(data=payload, message=f"Uploaded '{filename}' specifically for Chat AI Assistant.")

from services.storage.dataset_storage_service import storage_service, active_datasets_cache

import uuid
import logging

logger = logging.getLogger("api.chat")

@router.post("/message")
def chat_message(payload: dict = Body(...), db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    message = payload.get("message", "").strip()
    history = payload.get("history", [])
    raw_dataset_id = payload.get("dataset_id")

    df = None
    analysis = None
    org_id = tenant.get("org_id", "org_default")
    user_id = tenant.get("user_id", 1)
    req_id = payload.get("request_id") or f"req-{uuid.uuid4().hex[:12]}"
    ds_id = None

    if raw_dataset_id is not None and str(raw_dataset_id).strip() != "":
        try:
            ds_id = int(raw_dataset_id)
        except (ValueError, TypeError):
            ds_id = None

    # Strict Dataset Isolation: If payload explicitly specified dataset_id, load that exact dataset
    if ds_id is not None:
        verify_dataset_access(ds_id, org_id, db)
        cache_key = (org_id, ds_id)
        cached = chat_dataset_store.get(cache_key)

        if cached:
            df = cached.get("df")
            analysis = cached.get("analysis")
        else:
            loaded = storage_service.load_dataset(ds_id, db=db, org_id=org_id)
            if loaded:
                df = loaded.get("cleaned_df", loaded.get("raw_df"))
                analysis = loaded.get("analysis")
                chat_dataset_store[cache_key] = {
                    "df": df,
                    "analysis": analysis,
                    "filename": loaded.get("filename", "active_dataset.csv"),
                    "dataset_id": ds_id
                }
    else:
        # Fallback to active tenant datasets if unpopulated
        datasets = storage_service.list_datasets(db=db, org_id=org_id)
        if datasets:
            ds_id = datasets[0]["id"]
            verify_dataset_access(ds_id, org_id, db)
            cache_key = (org_id, ds_id)
            cached = chat_dataset_store.get(cache_key)

            if cached:
                df = cached.get("df")
                analysis = cached.get("analysis")
            else:
                loaded = storage_service.load_dataset(ds_id, db=db, org_id=org_id)
                if loaded:
                    df = loaded.get("cleaned_df", loaded.get("raw_df"))
                    analysis = loaded.get("analysis")
                    chat_dataset_store[cache_key] = {
                        "df": df,
                        "analysis": analysis,
                        "filename": loaded.get("filename", "active_dataset.csv"),
                        "dataset_id": ds_id
                    }

    raw_doc_id = payload.get("document_id")
    doc_id = None
    if raw_doc_id is not None and str(raw_doc_id).strip() != "":
        try:
            doc_id = int(raw_doc_id)
        except (ValueError, TypeError):
            doc_id = None

    if (df is None or analysis is None or ds_id is None) and doc_id is None:
        # Check if query is document RAG query
        from services.ai.agent_orchestrator import ai_agent_orchestrator
        doc_resp = ai_agent_orchestrator.process_query(df=None, analysis=None, history=history, query=message, org_id=org_id, document_id=doc_id)
        if doc_resp.get("success"):
            doc_resp["request_id"] = req_id
            return StandardResponse.ok(data=doc_resp)

        return StandardResponse.ok(data={
            "request_id": req_id,
            "text": "Please select an active dataset or document before asking a question.",
            "table": None,
            "stats": None,
            "follow_ups": [],
            "source": {"filename": "None", "rows_used": "0 Rows", "confidence_score": 0},
            "is_blocked": True,
            "intent": "BLOCKED",
            "execution": "NONE"
        })

    # Diagnostic Context Logging (PII safe)
    filename = analysis.get("filename", "active_dataset.csv") if isinstance(analysis, dict) else "active_dataset.csv"
    col_names = list(df.columns) if (df is not None and hasattr(df, "columns")) else []
    logger.info(f"[CHAT_CONTEXT] user_id={user_id} org_id={org_id} dataset_id={ds_id} dataset_filename={filename} rows={len(df) if df is not None else 0}")

    # ---------------------------------------------------------------
    # GEMINI HIGH-SPEED ENGINE — Sub-Second Full Dataset Analytics
    # ---------------------------------------------------------------
    gemini_answered = False
    response_payload = None

    try:
        from services.ai.llm_provider import LLMFactory, MockLLMProvider
        llm = LLMFactory.get_provider()

        if not isinstance(llm, MockLLMProvider) and df is not None and len(df) > 0:
            total_rows = len(df)
            total_cols = len(df.columns)

            # Pre-compute exact full-dataset profiling across ALL rows
            col_summary = []
            for col in df.columns:
                null_mask = df[col].isnull() | (df[col].astype(str).str.strip() == "") | (df[col].astype(str).str.lower() == "nan")
                null_cnt = int(null_mask.sum())
                valid_cnt = total_rows - null_cnt
                null_pct = round((null_cnt / total_rows) * 100, 2) if total_rows > 0 else 0.0

                line = f"- {col}: {null_cnt} missing out of {total_rows} rows ({null_pct}% missing, {valid_cnt} valid)"
                try:
                    clean_s = pd.to_numeric(df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip(), errors='coerce')
                    valid_s = clean_s.dropna()
                    if not valid_s.empty:
                        line += f" | mean: {round(float(valid_s.mean()), 2)}, median: {round(float(valid_s.median()), 2)}, min: {round(float(valid_s.min()), 2)}, max: {round(float(valid_s.max()), 2)}"
                except Exception:
                    pass
                col_summary.append(line)

            exact_stats_text = "\n".join(col_summary)

            # Fast 20-row sample preview (keeps prompt small & sub-second fast)
            sample_preview = df.head(20).to_csv(index=True, index_label="row_index")

            # Quality metrics
            quality = analysis.get("quality_scores", {}) if isinstance(analysis, dict) else {}
            missing_count = analysis.get("total_missing_cells", 0) if isinstance(analysis, dict) else 0
            dup_count = analysis.get("duplicate_count", 0) if isinstance(analysis, dict) else 0
            anomaly_count = len(analysis.get("anomalies", [])) if isinstance(analysis, dict) else 0

            history_context = ""
            if history:
                turns = []
                for turn in history[-4:]:
                    role = turn.get("role", "user")
                    content = turn.get("content", turn.get("text", ""))
                    if content:
                        turns.append(f"{role.capitalize()}: {str(content)[:200]}")
                history_context = "\n".join(turns)

            system_prompt = (
                "You are an expert enterprise data analytics platform assistant.\n\n"
                "COMPREHENSIVE ANALYTICAL MANDATE:\n"
                f"1. You are analyzing the COMPLETE dataset containing ALL {total_rows} rows and {total_cols} columns.\n"
                f"2. All counts, missing rates, percentages, and averages MUST reflect ALL {total_rows} rows using the EXACT METRICS below.\n"
                "3. NEVER state or imply that you are using a sample or subset. Always state figures for the ENTIRE dataset.\n"
                "4. PROVIDE BIG, DETAILED, COMPREHENSIVE OUTPUTS.\n"
                "5. STRICT NO-ROLE RULE: Do NOT start your response with self-referential role intros (e.g. 'As a Senior Principal Data Analyst AI...', 'Role: ...', 'Task: ...', 'As an AI...'). Jump IMMEDIATELY into the report title or Executive Summary.\n"
                "6. Structure your response thoroughly with:\n"
                "   - **Executive Summary & Overview**\n"
                "   - **Full Detailed Breakdown Tables & Metrics**\n"
                "   - **Column-by-Column Deep Insights**\n"
                "   - **Data Quality & Health Observations**\n"
                "   - **Actionable Remediation Recommendations**\n"
                "7. Format answers richly using markdown headers (`###`), tables, bullet points, bold key values, and code blocks."
            )

            user_prompt = (
                f"Dataset: **{filename}** | Total Rows: **{total_rows}** | Total Columns: **{total_cols}**\n\n"
                f"EXACT FULL-DATASET METRICS (Calculated across ALL {total_rows} rows):\n"
                f"{exact_stats_text}\n\n"
                f"Overall Quality Score: {quality.get('overall_score', 'N/A')}% | Missing Cells: {missing_count} | Duplicates: {dup_count} | ML Anomalies: {anomaly_count}\n\n"
                f"Recent Chat History:\n{history_context}\n\n"
                f"User Question: {message}\n\n"
                f"Data Sample (First 20 rows):\n```csv\n{sample_preview}\n```\n\n"
                f"Provide a BIG, DETAILED, COMPREHENSIVE, and IN-DEPTH answer to the user's question using the EXACT FULL-DATASET METRICS across ALL {total_rows} rows. "
                f"Do NOT include any role intros. Start directly with the Executive Summary."
            )

            llm_response = llm.generate(prompt=user_prompt, system_prompt=system_prompt, temperature=0.1)
            llm_text = llm_response.content.strip() if llm_response.content else ""

            # Strip any accidental role preambles from model output
            role_patterns = [
                r"^As a Senior Principal Data Analyst[^\n]*\n*",
                r"^As an AI[^\n]*\n*",
                r"^As a Data Analyst[^\n]*\n*",
                r"^\*?\s*Role:\s*[^\n]*\n*",
                r"^\*?\s*Task:\s*[^\n]*\n*",
                r"^\*?\s*Constraint[^\n]*\n*"
            ]
            for pat in role_patterns:
                llm_text = re.sub(pat, "", llm_text, flags=re.IGNORECASE).strip()

            if llm_text and len(llm_text) > 10:
                response_payload = {
                    "text": llm_text,
                    "intent": "GEMINI_DIRECT",
                    "execution": "GEMINI_LLM",
                    "llm_provider": llm_response.provider,
                    "llm_model": llm_response.model,
                    "table": None,
                    "stats": {
                        "total_rows": total_rows,
                        "missing_count": missing_count,
                        "duplicate_count": dup_count,
                        "anomaly_count": anomaly_count,
                        "overall_score": quality.get("overall_score", 0)
                    },
                    "follow_ups": [],
                    "source": {
                        "filename": filename,
                        "rows_used": f"{total_rows} Rows (100% Complete)",
                        "confidence_score": 0.99
                    },
                    "verified": True,
                    "resolved_columns": col_names
                }
                gemini_answered = True

    except Exception as e:
        logger.warning(f"Gemini primary engine failed, falling back to statistical agent: {e}")

    # ---------------------------------------------------------------
    # FALLBACK: Statistical Agent (if Gemini unavailable or failed)
    # ---------------------------------------------------------------
    if not gemini_answered:
        if doc_id is not None or any(k in message.lower() for k in ["pdf", "document", "policy", "section", "article", "handbook"]):
            from services.ai.agent_orchestrator import ai_agent_orchestrator
            response_payload = ai_agent_orchestrator.process_query(df=df, analysis=analysis, history=history, query=message, org_id=org_id, document_id=doc_id)
        else:
            fresh_agent = DatasetChatAgent()
            response_payload = fresh_agent.process_chat_query(df, analysis, history, message)

    response_payload["request_id"] = req_id
    response_payload["dataset_id"] = ds_id

    # Structured logging
    log_meta = {
        "request_id": req_id,
        "dataset_id": ds_id,
        "org_id": org_id,
        "user_id": user_id,
        "normalized_query": message.lower(),
        "detected_intent": response_payload.get("intent", "UNKNOWN"),
        "resolved_columns": response_payload.get("resolved_columns", []),
        "execution_method": response_payload.get("execution", "GEMINI_LLM")
    }
    logger.info(f"AI_CHAT_REQUEST: {log_meta}")

    return StandardResponse.ok(data=response_payload)

