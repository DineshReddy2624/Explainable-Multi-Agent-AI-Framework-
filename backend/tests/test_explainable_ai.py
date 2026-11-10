import sys
import os
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.abspath("backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from core.database import SessionLocal, engine, Base
from models.dataset import Dataset
from services.ai.explainable_ai_service import explainable_ai_service

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_explainable_ai_service_generation():
    """Test Explainable AI service row-by-row synthesis logic."""
    db = SessionLocal()
    try:
        db_ds = Dataset(
            id=777,
            org_id="org_default",
            filename="xai_test_dataset.csv",
            file_path="xai_test_path.csv",
            file_size=200.0,
            file_type="csv",
            status="PROFILED"
        )
        db.merge(db_ds)
        db.commit()

        res = explainable_ai_service.generate_xai_explanations(777, db=db, org_id="org_default")
        assert "summary" in res
        assert "explanations" in res
        assert res["dataset_id"] == 777

        llm_res = explainable_ai_service.explain_row_with_llm(
            dataset_id=777,
            row_index=5,
            column_name="Salary",
            issue_type="ML_ANOMALY",
            raw_value="-5000",
            db=db,
            org_id="org_default"
        )
        assert llm_res["row_index"] == 5
        assert "Deep Explainable AI Analysis" in llm_res["title"]

    finally:
        db.close()


def test_explainable_ai_api_endpoints():
    """Test /api/v1/explainable-ai/xai-explanations and /explain-row endpoints."""
    headers = {"Authorization": "Bearer mock_test_token"}

    res = client.get("/api/v1/explainable-ai/xai-explanations/777", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "summary" in data

    post_payload = {
        "dataset_id": 777,
        "row_index": 12,
        "column_name": "Email",
        "issue_type": "SYNTAX_ERROR",
        "raw_value": "userdomain.com"
    }
    res_post = client.post("/api/v1/explainable-ai/explain-row", json=post_payload, headers=headers)
    assert res_post.status_code == 200
    data_post = res_post.json()["data"]
    assert data_post["row_index"] == 12
    assert "Email" in data_post["column_name"]
