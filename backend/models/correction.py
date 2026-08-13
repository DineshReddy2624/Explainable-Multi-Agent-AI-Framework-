from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from core.database import Base

class Correction(Base):
    __tablename__ = "corrections"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"), nullable=False)
    issue_type = Column(String, nullable=False)
    column_name = Column(String, nullable=False)
    recommended_action = Column(String, nullable=False) # IMPUTE_MEDIAN, DROP_DUPLICATES, CONVERT_ISO_DATE
    confidence_score = Column(Float, nullable=False)
    status = Column(String, default="RECOMMENDED") # RECOMMENDED, APPROVED, REJECTED, APPLIED
    applied_at = Column(DateTime, nullable=True)
