import os
import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from core.config import settings
from core.database import get_db
from core.response import StandardResponse
from services.agents.dynamic_analyzer import DynamicDatasetAnalyzer
from services.agents.dynamic_remediator import DynamicDatasetRemediator
from services.storage.dataset_storage_service import storage_service, active_datasets_cache

from core.tenant_security import get_tenant_context, verify_dataset_access, log_audit_event
from core.rbac import require_permission

router = APIRouter()
analyzer = DynamicDatasetAnalyzer()
remediator = DynamicDatasetRemediator()

from core.file_security import validate_uploaded_file

@router.post("/analyze-file")
async def analyze_uploaded_file(file: UploadFile = File(...), db: Session = Depends(get_db), tenant: dict = Depends(require_permission("dataset:create"))):
    filename = file.filename
    content = await file.read()
    
    clean_filename = validate_uploaded_file(filename, content)

    try:
        saved_data = storage_service.save_dataset(
            filename=filename,
            content=content,
            db=db,
            org_id=tenant["org_id"],
            owner_user_id=tenant["user_id"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process and store dataset: {str(e)}")

    payload = {
        "dataset_id": saved_data["dataset_id"],
        "org_id": saved_data.get("org_id", tenant["org_id"]),
        "records": saved_data["records"],
        "analysis": saved_data["analysis"]
    }

    return StandardResponse.ok(data=payload, message=f"Analyzed '{filename}' for organization '{tenant['org_id']}' successfully.")

@router.post("/apply-remediation/{dataset_id}")
def apply_remediation_and_recalculate(dataset_id: int, payload: dict = Body(default={}), db: Session = Depends(get_db), tenant: dict = Depends(require_permission("dataset:clean"))):
    # Verify tenant ownership
    verify_dataset_access(dataset_id, tenant["org_id"], db)

    cached = storage_service.load_dataset(dataset_id, db=db, org_id=tenant["org_id"])
    if not cached:
        raise HTTPException(status_code=404, detail=f"Dataset #{dataset_id} not found in database or storage.")

    current_df = cached["raw_df"].copy()
    cell_edits = payload.get("cell_edits", [])
    strategies = payload.get("strategies", [])
    auto_remediate_all = payload.get("auto_remediate_all", False)

    # Apply remediation
    cleaned_df, logs = remediator.apply_remediation(current_df, cell_edits, strategies, auto_remediate_all=auto_remediate_all)
    
    # Save cleaned dataset persistently to disk and DB
    result_data = storage_service.save_cleaned_dataset(
        dataset_id=dataset_id,
        cleaned_df=cleaned_df,
        logs=logs,
        db=db,
        org_id=tenant["org_id"],
        user_id=tenant["user_id"]
    )

    return StandardResponse.ok(
        data=result_data,
        message="Applied AI corrections, imputed missing values, and saved persistent cleaned dataset!"
    )

@router.get("/detect-pii/{dataset_id}")
def detect_pii_for_dataset(dataset_id: int, db: Session = Depends(get_db), tenant: dict = Depends(require_permission("dataset:read"))):
    verify_dataset_access(dataset_id, tenant["org_id"], db)
    cached = storage_service.load_dataset(dataset_id, db=db, org_id=tenant["org_id"])
    if not cached:
        raise HTTPException(status_code=404, detail=f"Dataset #{dataset_id} not found.")

    pii_results = cached.get("pii_detected")
    if pii_results is None:
        from services.privacy.pii_detector import pii_detector
        pii_results = pii_detector.detect_pii_columns(cached["raw_df"])

    return StandardResponse.ok(
        data={"dataset_id": dataset_id, "pii_detected": pii_results},
        message=f"Detected {len(pii_results)} PII columns in dataset #{dataset_id}."
    )

@router.post("/apply-pii-masking/{dataset_id}")
def apply_pii_masking_to_dataset(dataset_id: int, db: Session = Depends(get_db), tenant: dict = Depends(require_permission("dataset:clean"))):
    verify_dataset_access(dataset_id, tenant["org_id"], db)
    result = storage_service.save_pii_masked_dataset(
        dataset_id=dataset_id,
        db=db,
        org_id=tenant["org_id"],
        user_id=tenant["user_id"]
    )
    return StandardResponse.ok(
        data=result,
        message=f"Applied PII masking to dataset #{dataset_id} as a new version."
    )

@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    datasets_list = storage_service.list_datasets(db=db, org_id=tenant["org_id"])
    return StandardResponse.ok(data=datasets_list, message=f"Retrieved persistent datasets for organization '{tenant['org_id']}'.")
