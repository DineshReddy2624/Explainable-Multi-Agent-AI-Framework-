from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.tenant_security import get_tenant_context, verify_dataset_access
from core.response import StandardResponse
from schemas.correction import CorrectionRequest
from services.storage.dataset_storage_service import storage_service
from services.agents.dynamic_remediator import DynamicDatasetRemediator

router = APIRouter()
remediator = DynamicDatasetRemediator()

@router.post("/suggest/{dataset_id}")
def suggest_corrections(dataset_id: int, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    verify_dataset_access(dataset_id, tenant["org_id"], db)
    loaded = storage_service.load_dataset(dataset_id, db=db, org_id=tenant["org_id"])
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Dataset #{dataset_id} not found.")

    analysis = loaded.get("analysis", {})
    missing_report = analysis.get("missing_report", [])
    
    suggestions = []
    for item in missing_report:
        col = item["column"]
        null_cnt = item["null_count"]
        med_val = item.get("suggested_median") or item.get("suggested_mode") or "Impute Median/Mode"
        suggestions.append({
            "column": col,
            "issue": f"{null_cnt} Missing Values ({item.get('missing_pct', 0)}%)",
            "action": f"Impute with {med_val}"
        })

    if not suggestions:
        suggestions.append({
            "column": "Dataset",
            "issue": "0 Missing Values",
            "action": "Dataset is 100% complete; no imputation required."
        })

    return StandardResponse.ok(
        data={"dataset_id": dataset_id, "suggestions": suggestions},
        message=f"Generated AI remediation suggestions for dataset #{dataset_id}."
    )

from core.rbac import require_permission

@router.post("/apply")
def apply_correction(req: CorrectionRequest, db: Session = Depends(get_db), tenant: dict = Depends(require_permission("dataset:clean"))):
    verify_dataset_access(req.dataset_id, tenant["org_id"], db)
    loaded = storage_service.load_dataset(req.dataset_id, db=db, org_id=tenant["org_id"])
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Dataset #{req.dataset_id} not found.")

    current_df = loaded["raw_df"].copy()
    strategy_item = {"col": req.target_column or (current_df.columns[0] if len(current_df.columns) > 0 else "col"), "strategy": req.strategy}
    cleaned_df, logs = remediator.apply_remediation(current_df, [], [strategy_item])

    result_data = storage_service.save_cleaned_dataset(
        dataset_id=req.dataset_id,
        cleaned_df=cleaned_df,
        logs=logs,
        db=db,
        org_id=tenant["org_id"],
        user_id=tenant["user_id"]
    )

    return StandardResponse.ok(
        data=result_data,
        message="Applied AI correction and saved persistent cleaned dataset!"
    )
