from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from datetime import datetime
from core.database import Base

class Dataset(Base):
    __tablename__ = "uploaded_datasets"
    __table_args__ = (
        Index("idx_dataset_org_created", "org_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String, nullable=False, index=True, default="org_default")
    owner_user_id = Column(Integer, nullable=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Float, nullable=False)
    file_type = Column(String, nullable=False)
    status = Column(String, default="INGESTED") # INGESTED, PROFILED, AUDITED, CLEANED
    cleaned_file_path = Column(String, nullable=True)
    version_number = Column(Integer, nullable=False, default=1)
    parent_version_id = Column(Integer, nullable=True)
    version_type = Column(String, nullable=False, default="ORIGINAL") # ORIGINAL, CLEANED, CORRECTED, DERIVED
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
