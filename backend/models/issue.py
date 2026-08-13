from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from core.database import Base

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"), nullable=False)
    issue_category = Column(String, nullable=False) # MISSING, DUPLICATE, FORMAT, SCHEMA
    column_name = Column(String, nullable=True)
    affected_count = Column(Integer, default=0)
    description = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
