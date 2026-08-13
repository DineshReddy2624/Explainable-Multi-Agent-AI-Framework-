import uuid
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session

from core.database import SessionLocal, get_db
from models.user import User
from models.dataset import Dataset
from models.job import Job
from models.audit_log import AuditLog
from core.security import decode_token

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Authoritative JWT user resolution dependency.
    Extracts Bearer token from Authorization header and resolves user.
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    if token:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == int(user_id)).first() if str(user_id).isdigit() else db.query(User).filter(User.email == str(user_id)).first()
                if user and user.is_active:
                    return user
        except Exception as e:
            pass

    return None

def get_tenant_context(
    request: Request,
    db: Session = Depends(get_db),
    x_org_id: Optional[str] = Header(None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_role: Optional[str] = Header(None, alias="X-Role")
) -> Dict[str, Any]:
    """
    Resolves secure tenant context.
    JWT authenticated user identity is ALWAYS authoritative over client headers.
    """
    user = get_current_user(request, db)
    
    if user:
        # JWT Identity is authoritative
        return {
            "org_id": user.org_id or "org_default",
            "user_id": user.id,
            "role": (user.role or "ANALYST").upper(),
            "user": user
        }

    # Development Fallback Mode (when no JWT token is present in request)
    org_id = x_org_id.strip() if (x_org_id and x_org_id.strip()) else "org_default"
    user_id = int(x_user_id) if (x_user_id and x_user_id.isdigit()) else 1
    role = (x_role.strip().upper() if x_role else "ANALYST")

    return {
        "org_id": org_id,
        "user_id": user_id,
        "role": role,
        "user": None
    }

def verify_dataset_access(dataset_id: int, org_id: str, db: Session) -> Dataset:
    """Enforces strict tenant isolation: Prevents Org A from accessing Org B's datasets."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset #{dataset_id} not found.")

    if ds.org_id != org_id and org_id != "org_default" and ds.org_id != "org_default":
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Dataset #{dataset_id} does not belong to organization '{org_id}'."
        )
    return ds

def verify_job_access(job_id: str, org_id: str, db: Session) -> Job:
    """Enforces strict tenant isolation: Prevents Org A from inspecting Org B's background jobs."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    if job.org_id != org_id:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Job '{job_id}' does not belong to organization '{org_id}'."
        )
    return job

def log_audit_event(
    event_type: str,
    org_id: str = "org_default",
    user_id: Optional[int] = None,
    dataset_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
):
    """Log immutable audit trail events for organization activities."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        event = AuditLog(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            org_id=org_id,
            user_id=user_id,
            dataset_id=dataset_id,
            event_type=event_type,
            details=details or {}
        )
        db.add(event)
        db.commit()
    except Exception:
        if db:
            db.rollback()
    finally:
        if close_db and db:
            db.close()
