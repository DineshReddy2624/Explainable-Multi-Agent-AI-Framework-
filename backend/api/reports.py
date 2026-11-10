import os
import io
import datetime
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from core.config import settings
from core.database import get_db
from core.tenant_security import get_tenant_context, verify_dataset_access
from core.response import StandardResponse
from models.generated_code import GeneratedCode
from services.storage.dataset_storage_service import storage_service
from services.agents.dynamic_analyzer import DynamicDatasetAnalyzer
from services.exporter.pdf_report import generate_before_after_pdf_bytes
from services.storage.code_storage_service import code_storage_service

router = APIRouter()
analyzer = DynamicDatasetAnalyzer()

def _get_analyses_and_logs(dataset_id: int, db: Session, org_id: str):
    loaded = storage_service.load_dataset(dataset_id, db=db, org_id=org_id)
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Dataset #{dataset_id} not found.")

    before_analysis = loaded.get("analysis", {})
    applied_logs = loaded.get("logs", [])
    filename = loaded.get("filename", f"dataset_{dataset_id}.csv")
    cleaned_df = loaded.get("cleaned_df")

    if cleaned_df is not None and not cleaned_df.empty:
        after_analysis = analyzer.analyze(cleaned_df, filename=filename)
    else:
        after_analysis = before_analysis

    return before_analysis, after_analysis, applied_logs, filename

def _upsert_generated_code(db: Session, dataset_id: int, user_id: int, org_id: str, code_type: str, title: str, description: str, code_content: str):
    import hashlib
    import datetime
    existing = db.query(GeneratedCode).filter(
        GeneratedCode.dataset_id == dataset_id,
        GeneratedCode.org_id == org_id,
        GeneratedCode.code_type == code_type
    ).first()

    digital_hash = "0x" + hashlib.sha256(code_content.encode('utf-8')).hexdigest()[:16].upper()

    if existing:
        existing.title = title
        existing.description = description
        existing.code_content = code_content
        existing.digital_hash = digital_hash
        existing.execution_status = "EXECUTED"
        existing.created_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        return code_storage_service.save_generated_code(
            db=db,
            dataset_id=dataset_id,
            user_id=user_id,
            org_id=org_id,
            code_type=code_type,
            title=title,
            description=description,
            code_content=code_content
        )

def _persist_generated_code_and_report(db: Session, dataset_id: int, org_id: str, filename: str, applied_logs: list, pdf_filename: str, pdf_bytes: bytes = None, user_id: int = None):
    """Helper to automatically save synthesized Python, SQL, and PDF report files into DB & reports directory."""
    try:
        py_script = code_storage_service.generate_python_remediation_script(dataset_id, filename, applied_logs)
        _upsert_generated_code(
            db=db,
            dataset_id=dataset_id,
            user_id=user_id,
            org_id=org_id,
            code_type="PYTHON_REMEDIATION_SCRIPT",
            title=f"Python Remediation Script - {filename}",
            description=f"Executable Pandas cleaning pipeline script for {filename}",
            code_content=py_script
        )

        sql_query = code_storage_service.generate_sql_transformation_query(dataset_id, filename, applied_logs)
        _upsert_generated_code(
            db=db,
            dataset_id=dataset_id,
            user_id=user_id,
            org_id=org_id,
            code_type="SQL_TRANSFORMATION_QUERY",
            title=f"SQL Transformation Script - {filename}",
            description=f"Enterprise SQL transformation query for {filename}",
            code_content=sql_query
        )

        reports_dir = os.path.abspath(settings.REPORTS_DIR)
        os.makedirs(reports_dir, exist_ok=True)
        pdf_disk_path = os.path.join(reports_dir, pdf_filename)

        if pdf_bytes:
            with open(pdf_disk_path, "wb") as f:
                f.write(pdf_bytes)

        _upsert_generated_code(
            db=db,
            dataset_id=dataset_id,
            user_id=user_id,
            org_id=org_id,
            code_type="BEFORE_AFTER_PDF",
            title=f"Executive Before & After PDF Report - {filename}",
            description=f"Client-ready enterprise data quality assessment and remediation PDF report for {filename}",
            code_content=f"Report File: {pdf_disk_path}"
        )

        code_storage_service.save_report_record(
            db=db,
            dataset_id=dataset_id,
            user_id=user_id,
            report_type="BEFORE_AFTER_PDF",
            file_path=pdf_disk_path
        )
    except Exception as e:
        print(f"Error persisting generated code/report to DB: {e}")

def _make_pdf_response(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    stream = io.BytesIO(pdf_bytes)
    fn_base = filename.rsplit('.', 1)[0]
    ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    download_fn = f"DataQuality_Before_After_{fn_base}_{ts_str}.pdf"
    response = StreamingResponse(stream, media_type="application/pdf")
    response.headers["Content-Disposition"] = f'attachment; filename="{download_fn}"'
    return response

@router.get("/generate/{dataset_id}")
def generate_report(dataset_id: int, format: str = "pdf", db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    verify_dataset_access(dataset_id, tenant["org_id"], db)

    if format.lower() == "pdf":
        before_analysis, after_analysis, applied_logs, filename = _get_analyses_and_logs(dataset_id, db, tenant["org_id"])

        pdf_bytes = generate_before_after_pdf_bytes(
            before_analysis=before_analysis,
            after_analysis=after_analysis,
            applied_logs=applied_logs,
            filename=filename,
            dataset_id=dataset_id,
            org_id=tenant["org_id"]
        )

        fn_base = filename.rsplit('.', 1)[0]
        ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_fn = f"DataQuality_Before_After_{fn_base}_{ts_str}.pdf"
        _persist_generated_code_and_report(db, dataset_id, tenant["org_id"], filename, applied_logs, pdf_fn, pdf_bytes=pdf_bytes, user_id=tenant.get("user_id"))

        return _make_pdf_response(pdf_bytes, filename)

    return StandardResponse.ok(data={
        "dataset_id": dataset_id,
        "format": format,
        "report_url": f"/api/v1/export/{dataset_id}?format={format}"
    }, message=f"Generated {format.upper()} executive report successfully.")

@router.post("/before-after-pdf")
def generate_before_after_pdf_custom(payload: dict = Body(...), db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    dataset_id = payload.get("dataset_id", 1)
    filename = payload.get("filename", "uploaded_dataset.csv")
    before_analysis = payload.get("before_analysis") or payload.get("analysis") or {}
    after_analysis = payload.get("after_analysis") or payload.get("analysis") or {}
    applied_logs = payload.get("applied_logs") or []

    pdf_bytes = generate_before_after_pdf_bytes(
        before_analysis=before_analysis,
        after_analysis=after_analysis,
        applied_logs=applied_logs,
        filename=filename,
        dataset_id=dataset_id,
        org_id=tenant["org_id"]
    )

    fn_base = filename.rsplit('.', 1)[0]
    ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_fn = f"DataQuality_Before_After_{fn_base}_{ts_str}.pdf"
    _persist_generated_code_and_report(db, dataset_id, tenant["org_id"], filename, applied_logs, pdf_fn, pdf_bytes=pdf_bytes, user_id=tenant.get("user_id"))

    return _make_pdf_response(pdf_bytes, filename)

@router.get("/before-after-pdf/{dataset_id}")
def generate_before_after_pdf(dataset_id: int, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    verify_dataset_access(dataset_id, tenant["org_id"], db)
    before_analysis, after_analysis, applied_logs, filename = _get_analyses_and_logs(dataset_id, db, tenant["org_id"])

    pdf_bytes = generate_before_after_pdf_bytes(
        before_analysis=before_analysis,
        after_analysis=after_analysis,
        applied_logs=applied_logs,
        filename=filename,
        dataset_id=dataset_id,
        org_id=tenant["org_id"]
    )

    fn_base = filename.rsplit('.', 1)[0]
    ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_fn = f"DataQuality_Before_After_{fn_base}_{ts_str}.pdf"
    _persist_generated_code_and_report(db, dataset_id, tenant["org_id"], filename, applied_logs, pdf_fn, pdf_bytes=pdf_bytes, user_id=tenant.get("user_id"))

    return _make_pdf_response(pdf_bytes, filename)






