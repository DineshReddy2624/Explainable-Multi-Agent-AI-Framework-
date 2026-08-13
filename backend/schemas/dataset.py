from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class DatasetBase(BaseModel):
    filename: str
    file_size: float
    file_type: str

class DatasetResponse(DatasetBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class DatasetDetailResponse(DatasetResponse):
    row_count: Optional[int] = 0
    column_count: Optional[int] = 0
    column_names: Optional[List[str]] = []
    datatype_summary: Optional[Dict[str, str]] = {}
