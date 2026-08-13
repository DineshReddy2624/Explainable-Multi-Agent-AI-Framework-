from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from core.database import Base

class MonitoringMetric(Base):
    __tablename__ = "monitoring_metrics"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    status = Column(String, default="HEALTHY")
    timestamp = Column(DateTime, default=datetime.utcnow)
