from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.tenant_security import get_tenant_context, verify_dataset_access
from core.response import StandardResponse
from schemas.chatbot import ChatQueryRequest
from services.storage.dataset_storage_service import storage_service
from services.agents.dataset_chat_agent import DatasetChatAgent

router = APIRouter()
chat_agent = DatasetChatAgent()

@router.post("/query")
def query_chatbot(req: ChatQueryRequest, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    if req.dataset_id:
        verify_dataset_access(req.dataset_id, tenant["org_id"], db)
        loaded = storage_service.load_dataset(req.dataset_id, db=db, org_id=tenant["org_id"])
    else:
        datasets = storage_service.list_datasets(db=db, org_id=tenant["org_id"])
        loaded = storage_service.load_dataset(datasets[0]["id"], db=db, org_id=tenant["org_id"]) if datasets else None

    if not loaded:
        return StandardResponse.ok(data={
            "dataset_id": req.dataset_id,
            "query": req.query,
            "answer": "No dataset found. Please upload a dataset to begin chat analysis.",
            "suggested_questions": ["How do I upload a dataset?"]
        })

    df = loaded.get("cleaned_df", loaded.get("raw_df"))
    analysis = loaded.get("analysis", {})
    res = chat_agent.process_chat_query(df, analysis, [], req.query)

    return StandardResponse.ok(data={
        "dataset_id": req.dataset_id,
        "query": req.query,
        "answer": res.get("text", ""),
        "suggested_questions": res.get("follow_ups", [])
    })
