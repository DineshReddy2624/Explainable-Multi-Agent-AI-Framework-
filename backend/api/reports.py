from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.tenant_security import get_tenant_context, verify_dataset_access
from core.response import StandardResponse
from services.storage.dataset_storage_service import storage_service

router = APIRouter()

@router.get("/generate/{dataset_id}")
def generate_report(dataset_id: int, format: str = "pdf", db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    verify_dataset_access(dataset_id, tenant["org_id"], db)
    loaded = storage_service.load_dataset(dataset_id, db=db, org_id=tenant["org_id"])
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Dataset #{dataset_id} not found.")

    return StandardResponse.ok(data={
        "dataset_id": dataset_id,
        "format": format,
        "report_url": f"/api/v1/export/{dataset_id}?format={format}"
    }, message=f"Generated {format.upper()} executive report successfully.")
