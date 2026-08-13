from pydantic import BaseModel
from typing import Optional

class CorrectionRequest(BaseModel):
    dataset_id: int
    issue_type: str
    strategy: str # MEAN, MEDIAN, MODE, DROP, REGEX_REPLACE

class CorrectionResponse(BaseModel):
    id: int
    dataset_id: int
    issue_type: str
    strategy: str
    status: str
    cleaned_dataset_path: Optional[str] = None

    model_config = {"from_attributes": True}
