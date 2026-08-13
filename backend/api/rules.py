from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.tenant_security import get_tenant_context
from core.response import StandardResponse
from schemas.rule import RuleCreate, RuleResponse

router = APIRouter()

rules_db_store = [
    {
        "id": 1,
        "rule_name": "Age Non-Negative Check",
        "target_column": "age",
        "rule_type": "RANGE",
        "parameters": {"min": 0, "max": 120},
        "is_active": True
    },
    {
        "id": 2,
        "rule_name": "Email Format Verification",
        "target_column": "email",
        "rule_type": "REGEX",
        "parameters": {"pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"},
        "is_active": True
    }
]

@router.post("")
@router.post("/")
def create_rule(rule: RuleCreate, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    new_rule = {
        "id": len(rules_db_store) + 1,
        "rule_name": rule.rule_name,
        "target_column": rule.target_column,
        "rule_type": rule.rule_type,
        "parameters": rule.parameters or {},
        "is_active": True,
        "org_id": tenant["org_id"]
    }
    rules_db_store.append(new_rule)
    return StandardResponse.ok(data=new_rule, message=f"Rule '{rule.rule_name}' created successfully.")

@router.get("")
@router.get("/")
def list_rules(db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    return StandardResponse.ok(data=rules_db_store, message="Retrieved active quality rules.")
