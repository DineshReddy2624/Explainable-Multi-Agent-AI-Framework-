from pydantic import BaseModel
from datetime import datetime

class ReportResponse(BaseModel):
    id: int
    dataset_id: int
    report_type: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True
