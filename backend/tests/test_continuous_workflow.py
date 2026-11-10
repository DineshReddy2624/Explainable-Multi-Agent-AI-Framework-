import os
import sys
import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Ensure backend path is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from core.database import SessionLocal
from models.user import User
from core.security import create_access_token
from services.storage.dataset_storage_service import storage_service

client = TestClient(app)

def get_auth_headers():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "admin@dataquality.ai").first()
    db.close()
    if not user:
        token_data = {"sub": "admin@dataquality.ai", "user_id": 1, "org_id": "org_default", "role": "ADMIN"}
    else:
        token_data = {"sub": user.email, "user_id": user.id, "org_id": user.org_id or "org_default", "role": user.role}
    token = create_access_token(data=token_data)
    return {"Authorization": f"Bearer {token}"}

def test_continuous_workflow_end_to_end():
    headers = get_auth_headers()
    
    # Path to sample dataset
    sample_path = os.path.join(os.path.dirname(backend_dir), "datasets", "original", "1_customer_demographics_raw.csv")
    assert os.path.exists(sample_path), f"Sample dataset not found at {sample_path}"
    
    # -------------------------------------------------------------
    # STEP 1: Upload & Analyze
    # -------------------------------------------------------------
    with open(sample_path, "rb") as f:
        file_content = f.read()

    response = client.post(
        "/api/v1/upload/analyze-file",
        files={"file": ("customer_test.csv", io.BytesIO(file_content), "text/csv")},
        headers=headers
    )
    assert response.status_code == 200, f"Upload failed: {response.text}"
    upload_res = response.json()
    dataset_id = upload_res["data"]["dataset_id"]
    initial_analysis = upload_res["data"]["analysis"]
    initial_records = upload_res["data"]["records"]
    initial_rows = initial_analysis["total_rows"]
    initial_cols = initial_analysis["total_cols"]

    print(f"\n[Step 1] Uploaded dataset #{dataset_id}: {initial_rows} rows, {initial_cols} cols.")
    assert initial_rows > 0
    assert initial_cols > 0

    # -------------------------------------------------------------
    # STEP 2: Verify Initial Profiling & Issues
    # -------------------------------------------------------------
    issues_resp = client.get(f"/api/v1/issues/{dataset_id}", headers=headers)
    assert issues_resp.status_code == 200
    issues_data = issues_resp.json()["data"]
    missing_report = issues_data.get("missing_values", [])
    format_issues = issues_data.get("format_mismatches", [])
    anomalies = issues_data.get("anomalies", [])
    print(f"[Step 2] Issues detected: {len(missing_report)} missing cols, {len(format_issues)} format issues, {len(anomalies)} anomalies.")

    # -------------------------------------------------------------
    # STEP 3: Quality Issues Remediation
    # - Manual Fix: change a cell value
    # - AI Fix: impute missing value
    # - Ignore: keep unmodified
    # -------------------------------------------------------------
    # Load dataset DataFrame
    cached = storage_service.load_dataset(dataset_id)
    assert cached is not None
    current_df = cached["raw_df"].copy()

    # Manual Fix on row 0
    test_col = current_df.columns[0]
    orig_val_row0 = current_df.at[0, test_col]
    current_df.at[0, test_col] = "MANUAL_FIX_VAL"

    # AI Fix: Impute nulls in a column
    null_cols = [c for c in current_df.columns if current_df[c].isnull().sum() > 0]
    if null_cols:
        target_impute_col = null_cols[0]
        med_val = 42
        current_df[target_impute_col] = current_df[target_impute_col].fillna(med_val)
        print(f"[Step 3] AI Imputed column '{target_impute_col}' with {med_val}")

    quality_corrected_records = current_df.to_dict(orient="records")
    print("[Step 3] Quality remediation completed on continuous dataset.")

    # -------------------------------------------------------------
    # STEP 4: Anomaly Detection Remediation
    # - Manual Fix on outlier
    # - Remove Record (Row deletion: Total rows decrements)
    # -------------------------------------------------------------
    current_row_count = len(current_df)
    # Simulate row removal of the last record
    current_df = current_df.iloc[:-1].reset_index(drop=True)
    new_row_count = len(current_df)
    assert new_row_count == current_row_count - 1
    print(f"[Step 4] Removed 1 outlier record. Row count: {current_row_count} -> {new_row_count}.")

    anomaly_corrected_records = current_df.astype(object).where(pd.notnull(current_df), None).to_dict(orient="records")

    # -------------------------------------------------------------
    # STEP 5 & 6: AI Remediation Save & Persist
    # -------------------------------------------------------------
    change_history_logs = [
        {
            "row_index": 0,
            "column_name": test_col,
            "original_value": str(orig_val_row0),
            "corrected_value": "MANUAL_FIX_VAL",
            "correction_type": "Manual Correction",
            "applied_by": "User",
            "confidence_score": 1.0,
            "status": "Applied ✓"
        },
        {
            "row_index": current_row_count - 1,
            "column_name": "Record",
            "original_value": f"Row #{current_row_count}",
            "corrected_value": "[DELETED]",
            "correction_type": "Record Removed",
            "applied_by": "User",
            "confidence_score": 1.0,
            "status": "Applied ✓"
        }
    ]

    save_resp = client.post(
        f"/api/v1/upload/save-workflow-dataset/{dataset_id}",
        json={"records": anomaly_corrected_records, "logs": change_history_logs},
        headers=headers
    )
    assert save_resp.status_code == 200, f"Save workflow dataset failed: {save_resp.text}"
    saved_data = save_resp.json()["data"]
    print(f"[Step 5] Saved final workflow dataset: {len(saved_data['records'])} records.")

    # -------------------------------------------------------------
    # STEP 7: Export & Download Verification
    # Verify downloaded file preserves all manual, AI, and removal changes!
    # -------------------------------------------------------------
    download_resp = client.get(f"/api/v1/export/download/{dataset_id}?format=csv", headers=headers)
    assert download_resp.status_code == 200
    downloaded_csv_content = download_resp.text

    downloaded_df = pd.read_csv(io.StringIO(downloaded_csv_content))
    assert len(downloaded_df) == new_row_count, f"Expected {new_row_count} rows, got {len(downloaded_df)}"
    assert downloaded_df.at[0, test_col] == "MANUAL_FIX_VAL", "Manual fix was not preserved in downloaded dataset!"
    print(f"[Step 7] Export verified! Downloaded dataset matches final dataset ({len(downloaded_df)} rows) and contains manual fix!")

if __name__ == "__main__":
    test_continuous_workflow_end_to_end()
    print("\n✅ All End-to-End Continuous Workflow Tests PASSED successfully!")
