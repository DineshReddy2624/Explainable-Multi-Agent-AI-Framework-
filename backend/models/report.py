from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from core.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"), nullable=False)
    report_type = Column(String, nullable=False) # PDF, CSV, EXCEL
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
