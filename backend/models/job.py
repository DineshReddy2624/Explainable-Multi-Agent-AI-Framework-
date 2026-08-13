from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Index
from datetime import datetime
from core.database import Base

class Job(Base):
    __tablename__ = "background_jobs"
    __table_args__ = (
        Index("idx_job_org_status", "org_id", "status"),
        Index("idx_job_dataset_org", "dataset_id", "org_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    org_id = Column(String, nullable=False, index=True, default="org_default")
    owner_user_id = Column(Integer, nullable=True, index=True)
    celery_task_id = Column(String, nullable=True)
    dataset_id = Column(Integer, nullable=True, index=True)
    task_type = Column(String, nullable=False)
    status = Column(String, default="QUEUED", index=True) # QUEUED, RUNNING, SUCCESS, FAILED
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    result_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
