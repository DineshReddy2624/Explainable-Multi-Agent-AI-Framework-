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

@router.post("/save-workflow-dataset/{dataset_id}")
def save_workflow_dataset(
    dataset_id: int,
    payload: dict = Body(default={}),
    db: Session = Depends(get_db),
    tenant: dict = Depends(require_permission("dataset:clean"))
):
    """
    Permanently save the complete dataset workflow state.

    This is the core "Save Dataset" endpoint. It persists ALL 14 required items:
      A. Original Dataset (original_records)
      B. Final Modified Dataset (records)
      C. Dataset Versions (auto-created in DB)
      D. Profiling Results (before_analysis + after_analysis)
      E. Quality Issues (embedded in change_history + quality_decisions)
      F. Quality Corrections (quality_decisions)
      G. Anomaly Results (embedded in anomaly_decisions)
      H. Anomaly Corrections (anomaly_decisions)
      I. AI Remediation Results (applied_logs)
      J. Manual Corrections (change_history)
      K. AI Corrections (change_history)
      L. Ignored Issues (quality_decisions + anomaly_decisions)
      M. Complete Change History (change_history)
      N. Saved Report Metadata (dataset_metadata table)

    After this call, the dataset is permanently stored and survives:
    - Browser restart
    - Server restart
    - Computer restart / logout / login
    """
    verify_dataset_access(dataset_id, tenant["org_id"], db)

    records = payload.get("records", [])
    logs = payload.get("logs", [])

    if not records:
        raise HTTPException(status_code=400, detail="No records provided to persist.")

    # Build the workflow bundle from the full payload
    workflow_bundle = {
        "original_records": payload.get("original_records", []),
        "change_history": payload.get("change_history", []),
        "quality_decisions": payload.get("quality_decisions", {}),
        "anomaly_decisions": payload.get("anomaly_decisions", {}),
        "before_analysis": payload.get("before_analysis", {}),
        "after_analysis": payload.get("after_analysis", {}),
        "applied_logs": payload.get("applied_logs", logs),
    }

    import pandas as pd
    cleaned_df = pd.DataFrame(records)
    cleaned_df.columns = [str(c).strip() for c in cleaned_df.columns]

    result_data = storage_service.save_cleaned_dataset(
        dataset_id=dataset_id,
        cleaned_df=cleaned_df,
        logs=logs,
        db=db,
        org_id=tenant["org_id"],
        user_id=tenant["user_id"],
        workflow_bundle=workflow_bundle
    )

    return StandardResponse.ok(
        data=result_data,
        message=f"Dataset #{dataset_id} permanently saved with complete workflow bundle ({len(records)} rows, {len(workflow_bundle['change_history'])} change history entries)."
    )


@router.get("/workflow-bundle/{dataset_id}")
def get_workflow_bundle(
    dataset_id: int,
    db: Session = Depends(get_db),
    tenant: dict = Depends(require_permission("dataset:read"))
):
    """
    Retrieve the complete persisted workflow state for a saved dataset.

    Returns all 14 items (original records, final records, change history,
    quality decisions, anomaly decisions, before/after analysis, applied logs)
    so the frontend can fully restore the dataset state after any restart.
    """
    verify_dataset_access(dataset_id, tenant["org_id"], db)

    bundle = storage_service.load_workflow_bundle(
        dataset_id=dataset_id,
        db=db,
        org_id=tenant["org_id"]
    )

    if bundle is None:
        raise HTTPException(
            status_code=404,
            detail=f"No saved workflow bundle found for dataset #{dataset_id}. Use 'Save Dataset' first."
        )

    return StandardResponse.ok(
        data=bundle,
        message=f"Retrieved complete workflow bundle for dataset #{dataset_id}."
    )


@router.get("/datasets")
def list_datasets(
    saved_only: bool = False,
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    datasets_list = storage_service.list_datasets(db=db, org_id=tenant["org_id"], saved_only=saved_only)
    return StandardResponse.ok(data=datasets_list, message=f"Retrieved datasets for organization '{tenant['org_id']}'.")


@router.get("/saved-datasets")
def list_saved_datasets(
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    """
    Dedicated endpoint for the Saved Data & Reports Repository.
    Returns ONLY genuinely persisted cleaned datasets where:
      is_persisted = True AND artifact_type = 'CLEANED_DATASET' (with saved workflow bundle).
    """
    datasets_list = storage_service.list_datasets(db=db, org_id=tenant["org_id"], saved_only=True)
    return StandardResponse.ok(
        data=datasets_list,
        message=f"Retrieved {len(datasets_list)} saved cleaned datasets for organization '{tenant['org_id']}'."
    )


@router.delete("/datasets/{dataset_id}")
@router.delete("/{dataset_id}")
def delete_saved_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    tenant: dict = Depends(require_permission("dataset:delete"))
):
    """
    Permanently delete a saved dataset, all associated versions,
    profiling and quality records, workflow bundles, and underlying storage files.
    """
    verify_dataset_access(dataset_id, tenant["org_id"], db)
    success = storage_service.delete_dataset(dataset_id=dataset_id, db=db, org_id=tenant["org_id"])
    if not success:
        raise HTTPException(status_code=404, detail=f"Dataset #{dataset_id} not found.")

    from datetime import datetime
    log_audit_event(
        "DATASET_DELETED",
        org_id=tenant["org_id"],
        user_id=tenant.get("user_id"),
        dataset_id=dataset_id,
        db=db,
        details={"deleted_at": datetime.utcnow().isoformat()}
    )

    return StandardResponse.ok(
        data={"dataset_id": dataset_id, "deleted": True},
        message=f"Dataset #{dataset_id} and its associated workflow bundle permanently deleted."
    )




