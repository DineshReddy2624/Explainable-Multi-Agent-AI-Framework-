from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from core.database import Base

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"), nullable=False, index=True)
    org_id = Column(String, nullable=False, index=True, default="org_default")
    version_number = Column(Integer, nullable=False, default=1)
    parent_version_id = Column(Integer, nullable=True)
    version_type = Column(String, nullable=False, default="ORIGINAL") # ORIGINAL, CLEANED, CORRECTED, DERIVED
    file_path = Column(String, nullable=False)
    file_size = Column(Float, nullable=False, default=0.0)
    created_by_user_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
