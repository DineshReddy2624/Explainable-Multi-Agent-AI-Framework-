from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.response import StandardResponse
from models.job import Job

from core.tenant_security import get_tenant_context, verify_job_access, verify_dataset_access

router = APIRouter()

@router.get("/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    job = verify_job_access(job_id, tenant["org_id"], db)

    data = {
        "job_id": job.job_id,
        "org_id": job.org_id,
        "celery_task_id": job.celery_task_id,
        "dataset_id": job.dataset_id,
        "task_type": job.task_type,
        "status": job.status,
        "progress": job.progress,
        "error_message": job.error_message,
        "result_data": job.result_data,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }

    return StandardResponse.ok(data=data, message=f"Fetched job status for '{job_id}'")

@router.get("/dataset/{dataset_id}")
def list_dataset_jobs(dataset_id: int, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    verify_dataset_access(dataset_id, tenant["org_id"], db)
    jobs = db.query(Job).filter(Job.dataset_id == dataset_id, Job.org_id == tenant["org_id"]).order_by(Job.id.desc()).all()
    results = [
        {
            "job_id": j.job_id,
            "org_id": j.org_id,
            "task_type": j.task_type,
            "status": j.status,
            "progress": j.progress,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None
        }
        for j in jobs
    ]
    return StandardResponse.ok(data=results, message=f"Fetched job history for dataset #{dataset_id}")
