import os
import io
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from core.config import settings
from core.database import get_db
from services.storage.dataset_storage_service import storage_service
from core.tenant_security import get_tenant_context, verify_dataset_access

router = APIRouter()

@router.get("/{dataset_id}")
@router.get("/download/{dataset_id}")
def download_cleaned_dataset(dataset_id: int, format: str = "csv", mask_pii: bool = False, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    verify_dataset_access(dataset_id, tenant["org_id"], db)
    cached = storage_service.load_dataset(dataset_id, db=db, org_id=tenant["org_id"])
    
    if cached and "cleaned_df" in cached:
        df = cached["cleaned_df"].copy()
        filename_base = cached.get("filename", f"dataset_{dataset_id}").rsplit('.', 1)[0]
    else:
        tenant_cleaned_dir = os.path.join(settings.CLEANED_DIR, "organizations", tenant["org_id"])
        file_path = os.path.join(tenant_cleaned_dir, f"cleaned_dataset_{dataset_id}.csv")
        if not os.path.exists(file_path):
            file_path = os.path.join(settings.CLEANED_DIR, f"cleaned_dataset_{dataset_id}.csv")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Cleaned dataset file not found. Please apply corrections first.")
        import pandas as pd
        df = pd.read_csv(file_path)
        filename_base = f"dataset_{dataset_id}"

    # Only apply PII masking if explicitly requested via mask_pii=True
    if mask_pii:
        pii_cols = cached.get("pii_detected") if (cached and "pii_detected" in cached) else []
        if not pii_cols:
            from services.privacy.pii_detector import pii_detector
            pii_cols = pii_detector.detect_pii_columns(df)
        if pii_cols:
            from services.privacy.pii_masker import pii_masker
            from core.tenant_security import log_audit_event
            df, _ = pii_masker.mask_dataframe(df, pii_cols)
            log_audit_event("PII_MASKED_EXPORT", org_id=tenant["org_id"], user_id=tenant.get("user_id"), dataset_id=dataset_id, db=db)

    if format.lower() == "csv":
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = f"attachment; filename={filename_base}_cleaned.csv"
        return response
    elif format.lower() in ["excel", "xlsx"]:
        stream = io.BytesIO()
        df.to_excel(stream, index=False)
        stream.seek(0)
        response = StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = f"attachment; filename={filename_base}_cleaned.xlsx"
        return response
    elif format.lower() == "pdf":
        from services.exporter.pdf_report import generate_before_after_pdf_bytes
        before_analysis = cached.get("analysis", {}) if cached else {}
        after_analysis = cached.get("analysis", {}) if cached else {}
        applied_logs = cached.get("logs", []) if cached else []
        filename = cached.get("filename", f"dataset_{dataset_id}.csv") if cached else f"dataset_{dataset_id}.csv"

        pdf_bytes = generate_before_after_pdf_bytes(
            before_analysis=before_analysis,
            after_analysis=after_analysis,
            applied_logs=applied_logs,
            filename=filename,
            dataset_id=dataset_id,
            org_id=tenant["org_id"]
        )
        stream = io.BytesIO(pdf_bytes)
        response = StreamingResponse(stream, media_type="application/pdf")
        response.headers["Content-Disposition"] = f"attachment; filename={filename_base}_before_after_cleaning_report.pdf"
        return response
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format. Use csv, excel, or pdf.")

