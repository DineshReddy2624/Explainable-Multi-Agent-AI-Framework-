from pydantic import BaseModel
from typing import Optional, Dict, Any

class RuleCreate(BaseModel):
    rule_name: str
    target_column: str
    rule_type: str # RANGE, REGEX, NOT_NULL, UNIQUE
    parameters: Optional[Dict[str, Any]] = None

class RuleResponse(RuleCreate):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}
