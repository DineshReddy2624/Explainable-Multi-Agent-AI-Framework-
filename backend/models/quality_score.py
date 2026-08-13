from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from datetime import datetime
from core.database import Base

class QualityScore(Base):
    __tablename__ = "quality_scores"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    completeness = Column(Float, nullable=False)
    consistency = Column(Float, nullable=False)
    uniqueness = Column(Float, nullable=False)
    validity = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=False)
    timeliness = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
