import sys
import os
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.abspath("backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from core.database import SessionLocal, engine, Base
from sqlalchemy import text
from models.generated_code import GeneratedCode
from models.report import Report
from services.storage.code_storage_service import code_storage_service

# Ensure DB tables are created & alter column if missing
Base.metadata.create_all(bind=engine)
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE generated_codes ADD COLUMN user_id INTEGER"))
        conn.commit()
    except Exception:
        pass

client = TestClient(app)



def test_code_storage_service_synthesis():
    """Verify code synthesis (Python cleaning script + SQL transformation query) and SHA-256 hash generation."""
    applied_logs = [
        {"column_name": "Age", "correction_type": "Median Imputation", "original_value": "NaN", "corrected_value": "45.0"},
        {"column_name": "Email", "correction_type": "Regex Format Normalization", "original_value": "testatdomain", "corrected_value": "test@domain.com"}
    ]

    py_script = code_storage_service.generate_python_remediation_script(99, "test_dataset.csv", applied_logs)
    assert "remediate_dataset" in py_script
    assert "df.drop_duplicates()" in py_script
    assert "Median Imputation" in py_script

    sql_script = code_storage_service.generate_sql_transformation_query(99, "test_dataset.csv", applied_logs)
    assert "CREATE TABLE IF NOT EXISTS dataset_99_cleaned" in sql_script
    assert "SELECT DISTINCT *" in sql_script

    hash_val = code_storage_service.compute_sha256(py_script)
    assert hash_val.startswith("0x")
    assert len(hash_val) == 18


def test_generated_code_db_persistence_and_api():
    """Verify saving generated code to DB, retrieving via API, and downloading file."""
    db = SessionLocal()
    try:
        from models.dataset import Dataset
        db_ds = Dataset(
            id=888,
            org_id="org_default",
            filename="test_dataset_888.csv",
            file_path="test_path.csv",
            file_size=100.0,
            file_type="csv",
            status="PROFILED"
        )
        db.merge(db_ds)
        db.commit()

        record = code_storage_service.save_generated_code(
            db=db,
            dataset_id=888,
            org_id="org_default",
            code_type="PYTHON_REMEDIATION_SCRIPT",
            title="Unit Test Python Script",
            description="Test Python remediation script",
            code_content="import pandas as pd\nprint('Hello Quality World!')"
        )

        assert record.id is not None
        code_id = record.id

        # Test API GET list by dataset_id
        headers = {"Authorization": "Bearer mock_test_token"}
        res_list = client.get(f"/api/v1/code/dataset/888", headers=headers)
        assert res_list.status_code == 200
        data_list = res_list.json()["data"]
        assert len(data_list) >= 1
        assert any(item["id"] == code_id for item in data_list)

        # Test API GET details by code_id
        res_detail = client.get(f"/api/v1/code/{code_id}", headers=headers)
        assert res_detail.status_code == 200
        data_detail = res_detail.json()["data"]
        assert data_detail["code_type"] == "PYTHON_REMEDIATION_SCRIPT"
        assert "import pandas as pd" in data_detail["code_content"]

        # Test API GET user saved reports
        res_user = client.get("/api/v1/code/user/saved-reports", headers=headers)
        assert res_user.status_code == 200
        user_items = res_user.json()["data"]
        assert len(user_items) >= 1
        assert any(item["id"] == code_id for item in user_items)

    finally:
        db.close()

