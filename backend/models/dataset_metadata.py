from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from datetime import datetime
from core.database import Base

class DatasetMetadata(Base):
    __tablename__ = "dataset_metadata"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"), nullable=False, index=True)
    org_id = Column(String, nullable=False, index=True, default="org_default")
    total_rows = Column(Integer, default=0)
    total_columns = Column(Integer, default=0)
    column_names = Column(JSON, nullable=True)
    datatype_map = Column(JSON, nullable=True)
    stats_summary = Column(JSON, nullable=True)
    # workflow_bundle stores the complete persisted workflow state:
    # original_records, final_records, change_history, quality_decisions,
    # anomaly_decisions, before_analysis, after_analysis, applied_logs
    workflow_bundle = Column(JSON, nullable=True)
    # Path to the immutable original uploaded file (never overwritten)
    original_file_path = Column(String, nullable=True)
    # Timestamp when user explicitly clicked "Save Dataset"
    saved_at = Column(DateTime, nullable=True)
