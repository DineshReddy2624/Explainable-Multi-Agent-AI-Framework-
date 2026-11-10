import os
import io
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.tenant_security import get_tenant_context, verify_dataset_access
from core.response import StandardResponse
from models.generated_code import GeneratedCode
from services.storage.code_storage_service import code_storage_service

router = APIRouter()


@router.post("/save")
def save_generated_code_endpoint(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    """Save an AI-generated script or code snippet in the database."""
    dataset_id = payload.get("dataset_id", 1)
    verify_dataset_access(dataset_id, tenant["org_id"], db)

    code_type = payload.get("code_type", "PYTHON_REMEDIATION_SCRIPT")
    title = payload.get("title", "Generated Cleaning Script")
    description = payload.get("description", "Automated data remediation script")
    code_content = payload.get("code_content", "# Executable Python script")

    record = code_storage_service.save_generated_code(
        db=db,
        dataset_id=dataset_id,
        org_id=tenant["org_id"],
        code_type=code_type,
        title=title,
        description=description,
        code_content=code_content
    )

    return StandardResponse.ok(data={
        "id": record.id,
        "dataset_id": record.dataset_id,
        "code_type": record.code_type,
        "title": record.title,
        "digital_hash": record.digital_hash,
        "created_at": str(record.created_at)
    }, message="Generated code stored in database successfully.")


@router.get("/user/saved-reports")
def get_user_saved_reports(
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    """Retrieves all saved reports and database artifacts belonging to the authenticated user."""
    user_id = tenant.get("user_id")
    org_id = tenant.get("org_id", "org_default")

    # DB Cleanup: Remove historical duplicate rows for the same dataset and report type
    try:
        from sqlalchemy import func
        dups = db.query(GeneratedCode.dataset_id, GeneratedCode.code_type).group_by(GeneratedCode.dataset_id, GeneratedCode.code_type).having(func.count(GeneratedCode.id) > 1).all()
        for d_id, c_type in dups:
            all_recs = db.query(GeneratedCode).filter(
                GeneratedCode.dataset_id == d_id,
                GeneratedCode.code_type == c_type
            ).order_by(GeneratedCode.id.desc()).all()
            for old_rec in all_recs[1:]:
                db.delete(old_rec)
        db.commit()
    except Exception:
        db.rollback()

    query = db.query(GeneratedCode)
    if user_id:
        records = query.filter((GeneratedCode.user_id == user_id) | (GeneratedCode.org_id == org_id)).order_by(GeneratedCode.id.desc()).all()
    else:
        records = query.filter(GeneratedCode.org_id == org_id).order_by(GeneratedCode.id.desc()).all()

    seen_keys = set()
    items = []
    for r in records:
        dedup_key = f"{r.dataset_id}_{r.code_type}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)
        items.append({
            "id": r.id,
            "dataset_id": r.dataset_id,
            "user_id": r.user_id,
            "code_type": r.code_type,
            "title": r.title,
            "description": r.description,
            "digital_hash": r.digital_hash,
            "execution_status": r.execution_status,
            "created_at": str(r.created_at)
        })

    return StandardResponse.ok(data=items, message=f"Retrieved {len(items)} user saved report records.")


@router.get("/dataset/{dataset_id}")
def get_dataset_generated_codes(
    dataset_id: int,
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    """Retrieves all stored generated codes and scripts for a dataset or user."""
    user_id = tenant.get("user_id")
    org_id = tenant.get("org_id", "org_default")

    records = db.query(GeneratedCode).filter(GeneratedCode.dataset_id == dataset_id).order_by(GeneratedCode.id.desc()).all()
    if not records:
        if user_id:
            records = db.query(GeneratedCode).filter((GeneratedCode.user_id == user_id) | (GeneratedCode.org_id == org_id)).order_by(GeneratedCode.id.desc()).all()
        else:
            records = db.query(GeneratedCode).filter(GeneratedCode.org_id == org_id).order_by(GeneratedCode.id.desc()).all()

    seen_keys = set()
    items = []
    for r in records:
        dedup_key = f"{r.dataset_id}_{r.code_type}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)
        items.append({
            "id": r.id,
            "dataset_id": r.dataset_id,
            "user_id": r.user_id,
            "code_type": r.code_type,
            "title": r.title,
            "description": r.description,
            "digital_hash": r.digital_hash,
            "execution_status": r.execution_status,
            "created_at": str(r.created_at)
        })

    return StandardResponse.ok(data=items, message=f"Retrieved {len(items)} generated code records.")


@router.get("/{code_id}")
def get_generated_code_by_id(
    code_id: int,
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    """Retrieves details and source code for a specific generated code record."""
    record = db.query(GeneratedCode).filter(GeneratedCode.id == code_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Generated code #{code_id} not found.")

    verify_dataset_access(record.dataset_id, tenant["org_id"], db)

    return StandardResponse.ok(data={
        "id": record.id,
        "dataset_id": record.dataset_id,
        "org_id": record.org_id,
        "code_type": record.code_type,
        "title": record.title,
        "description": record.description,
        "code_content": record.code_content,
        "digital_hash": record.digital_hash,
        "execution_status": record.execution_status,
        "created_at": str(record.created_at)
    }, message="Retrieved generated code record successfully.")


@router.get("/download/{code_id}")
def download_generated_code_file(
    code_id: int,
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    """Downloads the stored generated code as an executable file (.py, .sql, or .pdf)."""
    record = db.query(GeneratedCode).filter(GeneratedCode.id == code_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Generated code #{code_id} not found.")

    verify_dataset_access(record.dataset_id, tenant["org_id"], db)

    if "PDF" in record.code_type.upper():
        if record.code_content and "Report File:" in record.code_content:
            disk_path = record.code_content.replace("Report File:", "").strip()
            if os.path.exists(disk_path):
                with open(disk_path, "rb") as f:
                    pdf_bytes = f.read()
                stream = io.BytesIO(pdf_bytes)
                response = StreamingResponse(stream, media_type="application/pdf")
                response.headers["Content-Disposition"] = f'attachment; filename="DataQuality_Report_{record.id}.pdf"'
                return response

        from services.storage.dataset_storage_service import storage_service
        from services.agents.dynamic_analyzer import DynamicDatasetAnalyzer
        from services.exporter.pdf_report import generate_before_after_pdf_bytes
        from models.dataset import Dataset
        from models.dataset_metadata import DatasetMetadata

        analyzer = DynamicDatasetAnalyzer()
        loaded = storage_service.load_dataset(record.dataset_id, db=db, org_id=tenant.get("org_id"))
        if not loaded:
            loaded = storage_service.load_dataset(record.dataset_id, db=db, org_id=None)

        db_dataset = db.query(Dataset).filter(Dataset.id == record.dataset_id).first()
        db_metadata = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == record.dataset_id).first()

        filename = loaded.get("filename") if loaded else (db_dataset.filename if db_dataset else f"dataset_{record.dataset_id}.csv")
        before_analysis = (loaded.get("analysis") if loaded else None) or (db_metadata.stats_summary if (db_metadata and db_metadata.stats_summary) else {})
        applied_logs = loaded.get("logs", []) if loaded else []
        cleaned_df = loaded.get("cleaned_df") if loaded else None
        after_analysis = analyzer.analyze(cleaned_df, filename=filename) if cleaned_df is not None and not cleaned_df.empty else before_analysis

        pdf_bytes = generate_before_after_pdf_bytes(
            before_analysis=before_analysis,
            after_analysis=after_analysis,
            applied_logs=applied_logs,
            filename=filename,
            dataset_id=record.dataset_id,
            org_id=tenant.get("org_id", "org_default")
        )
        fn_base = filename.rsplit('.', 1)[0]
        download_fn = f"DataQuality_Before_After_{fn_base}_report_{record.id}.pdf"
        stream = io.BytesIO(pdf_bytes)
        response = StreamingResponse(stream, media_type="application/pdf")
        response.headers["Content-Disposition"] = f'attachment; filename="{download_fn}"'
        return response

    ext = ".sql" if "SQL" in record.code_type else ".py"
    filename = f"{record.title.replace(' ', '_').lower()}_{record.id}{ext}"
    media_type = "application/sql" if ext == ".sql" else "text/x-python"

    stream = io.BytesIO(record.code_content.encode('utf-8'))
    response = StreamingResponse(stream, media_type=media_type)
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@router.get("/preview/{code_id}")
def preview_generated_pdf_report(
    code_id: int,
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    """Previews the stored PDF report directly in browser iframe with inline content disposition."""
    record = db.query(GeneratedCode).filter(GeneratedCode.id == code_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Generated report #{code_id} not found.")

    verify_dataset_access(record.dataset_id, tenant["org_id"], db)

    # 1. Directly serve stored PDF report file if present on disk
    if record.code_content and "Report File:" in record.code_content:
        disk_path = record.code_content.replace("Report File:", "").strip()
        if os.path.exists(disk_path):
            with open(disk_path, "rb") as f:
                pdf_bytes = f.read()
            stream = io.BytesIO(pdf_bytes)
            response = StreamingResponse(stream, media_type="application/pdf")
            response.headers["Content-Disposition"] = f'inline; filename="DataQuality_Report_{record.id}.pdf"'
            return response

    # 2. Re-generate report if disk file missing, using DB dataset metadata
    from services.storage.dataset_storage_service import storage_service
    from services.agents.dynamic_analyzer import DynamicDatasetAnalyzer
    from services.exporter.pdf_report import generate_before_after_pdf_bytes
    from models.dataset import Dataset
    from models.dataset_metadata import DatasetMetadata

    analyzer = DynamicDatasetAnalyzer()
    loaded = storage_service.load_dataset(record.dataset_id, db=db, org_id=tenant.get("org_id"))
    if not loaded:
        loaded = storage_service.load_dataset(record.dataset_id, db=db, org_id=None)

    db_dataset = db.query(Dataset).filter(Dataset.id == record.dataset_id).first()
    db_metadata = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == record.dataset_id).first()

    filename = loaded.get("filename") if loaded else (db_dataset.filename if db_dataset else f"dataset_{record.dataset_id}.csv")
    before_analysis = (loaded.get("analysis") if loaded else None) or (db_metadata.stats_summary if (db_metadata and db_metadata.stats_summary) else {})
    applied_logs = loaded.get("logs", []) if loaded else []
    cleaned_df = loaded.get("cleaned_df") if loaded else None
    after_analysis = analyzer.analyze(cleaned_df, filename=filename) if cleaned_df is not None and not cleaned_df.empty else before_analysis

    pdf_bytes = generate_before_after_pdf_bytes(
        before_analysis=before_analysis,
        after_analysis=after_analysis,
        applied_logs=applied_logs,
        filename=filename,
        dataset_id=record.dataset_id,
        org_id=tenant.get("org_id", "org_default")
    )
    fn_base = filename.rsplit('.', 1)[0]
    preview_fn = f"DataQuality_Before_After_{fn_base}_report_{record.id}.pdf"
    stream = io.BytesIO(pdf_bytes)
    response = StreamingResponse(stream, media_type="application/pdf")
    response.headers["Content-Disposition"] = f'inline; filename="{preview_fn}"'
    return response


@router.delete("/{code_id}")
def delete_generated_report(
    code_id: int,
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    """Delete a saved generated report/code entry from the database."""
    user_id = tenant.get("user_id")
    org_id = tenant.get("org_id", "org_default")

    record = db.query(GeneratedCode).filter(GeneratedCode.id == code_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Saved report not found.")

    if record.org_id and record.org_id != org_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this report.")

    if record.file_path and os.path.exists(record.file_path):
        try:
            os.remove(record.file_path)
        except Exception:
            pass

    db.delete(record)
    db.commit()

    return StandardResponse.ok(
        data={"id": code_id, "deleted": True},
        message=f"Report #{code_id} deleted successfully."
    )



