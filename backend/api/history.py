import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.tenant_security import get_tenant_context
from core.response import StandardResponse
from models.audit_log import AuditLog

router = APIRouter()

@router.get("/logs")
def get_history(db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    logs = db.query(AuditLog).filter(
        AuditLog.org_id == tenant["org_id"]
    ).order_by(AuditLog.created_at.desc()).limit(100).all()

    audit_entries = [
        {
            "id": l.id,
            "action": getattr(l, "event_type", "EVENT"),
            "description": json.dumps(l.details) if l.details else "Audit log entry",
            "user_id": l.user_id,
            "org_id": l.org_id,
            "timestamp": l.created_at.isoformat() if hasattr(l, "created_at") and l.created_at else "2026-08-08T00:00:00Z"
        }
        for l in logs
    ]
    return StandardResponse.ok(data=audit_entries, message=f"Retrieved audit log history for organization '{tenant['org_id']}'.")
