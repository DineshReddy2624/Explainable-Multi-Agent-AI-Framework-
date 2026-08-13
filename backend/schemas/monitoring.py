from pydantic import BaseModel
from datetime import datetime

class MonitoringMetricResponse(BaseModel):
    id: int
    dataset_id: int
    metric_name: str
    metric_value: float
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True
