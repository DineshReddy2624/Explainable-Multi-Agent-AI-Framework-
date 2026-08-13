from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    org_id = Column(String, nullable=False, index=True, default="org_default")
    user_id = Column(Integer, nullable=True, index=True)
    dataset_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
