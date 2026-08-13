from sqlalchemy import Column, Integer, String, ForeignKey, JSON
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
