from pydantic import BaseModel
from typing import Optional, List

class ChatQueryRequest(BaseModel):
    dataset_id: int
    query: str

class ChatQueryResponse(BaseModel):
    dataset_id: int
    query: str
    answer: str
    suggested_questions: Optional[List[str]] = []
