from pydantic import BaseModel
from typing import Optional, Dict, Any

class IssueResponse(BaseModel):
    id: int
    dataset_id: int
    issue_type: str
    column_name: Optional[str] = None
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
