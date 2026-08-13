from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from core.database import Base

class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"), nullable=False)
    algorithm = Column(String, default="Isolation Forest")
    row_index = Column(Integer, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    explanation = Column(String, nullable=True)
    shap_contributions = Column(JSON, nullable=True)
