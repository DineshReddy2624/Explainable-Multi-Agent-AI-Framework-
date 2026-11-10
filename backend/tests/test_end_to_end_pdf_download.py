import sys
import os
import pytest
import pandas as pd
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath("backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from services.agents.dynamic_analyzer import DynamicDatasetAnalyzer
from services.agents.dynamic_remediator import DynamicDatasetRemediator

client = TestClient(app)


def test_api_before_after_pdf_endpoint():
    """Verify that POST /api/v1/reports/before-after-pdf returns a valid application/pdf binary response."""
    payload = {
        "dataset_id": 678,
        "filename": "1_customer_demographics_raw.csv",
        "before_analysis": {
            "total_rows": 525,
            "total_cols": 8,
            "headers": ["Customer_ID", "Full_Name", "Age", "Email", "Phone", "Annual_Income", "Credit_Score", "Account_Status"],
            "datatype_map": {"Age": "float", "Annual_Income": "float", "Credit_Score": "float"},
            "missing_report": [{"column": "Age", "null_count": 130, "missing_pct": 24.76}],
            "total_missing_cells": 130,
            "duplicate_count": 25,
            "format_issues": [{"column": "Phone", "expected_format": "Wrong Phone Format", "invalid_value": "5551234567"}],
            "anomalies": [{"column": "Annual_Income", "value": 1250000.0}],
            "quality_scores": {"overall_score": 90.6, "completeness": 90.36, "uniqueness": 95.24, "validity": 84.45, "consistency": 91.05, "accuracy": 95.0}
        },
        "after_analysis": {
            "total_rows": 500,
            "total_cols": 8,
            "headers": ["Customer_ID", "Full_Name", "Age", "Email", "Phone", "Annual_Income", "Credit_Score", "Account_Status"],
            "datatype_map": {"Age": "float", "Annual_Income": "float", "Credit_Score": "float"},
            "missing_report": [],
            "total_missing_cells": 0,
            "duplicate_count": 0,
            "format_issues": [],
            "anomalies": [{"column": "Annual_Income", "value": 172666.48}],
            "quality_scores": {"overall_score": 99.5, "completeness": 100.0, "uniqueness": 100.0, "validity": 100.0, "consistency": 99.8, "accuracy": 95.0}
        },
        "applied_logs": [
            {"column_name": "Age", "correction_type": "Median Imputation", "original_value": "[NULL]", "corrected_value": "48.0"},
            {"column_name": "Phone", "correction_type": "Phone Format Standardization", "original_value": "5551234567", "corrected_value": "(555) 123-4567"}
        ]
    }

    headers = {"Authorization": "Bearer mock_test_token"}
    response = client.post("/api/v1/reports/before-after-pdf", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=\"DataQuality_Before_After_1_customer_demographics_raw_" in response.headers["content-disposition"]
    assert len(response.content) > 10000
    assert response.content.startswith(b"%PDF-")


def test_end_to_end_pdf_file_generation_and_validity():
    """Verify end-to-end dataset analysis, remediation, PDF rendering, and file disk creation."""
    raw_path = "datasets/original/1_customer_demographics_raw.csv"
    assert os.path.exists(raw_path)

    df_raw = pd.read_csv(raw_path)
    analyzer = DynamicDatasetAnalyzer()
    remediator = DynamicDatasetRemediator()

    before_analysis = analyzer.analyze(df_raw, filename="1_customer_demographics_raw.csv")
    df_cleaned, logs = remediator.apply_remediation(df_raw, cell_edits=[], strategies=[], auto_remediate_all=True)
    after_analysis = analyzer.analyze(df_cleaned, filename="1_customer_demographics_cleaned.csv")

    from services.exporter.pdf_report import generate_before_after_pdf_bytes

    pdf_bytes = generate_before_after_pdf_bytes(
        before_analysis=before_analysis,
        after_analysis=after_analysis,
        applied_logs=logs,
        filename="1_customer_demographics_raw.csv",
        dataset_id=678,
        org_id="org_default"
    )

    assert len(pdf_bytes) > 50000
    assert pdf_bytes.startswith(b"%PDF-")
    assert b"%EOF" in pdf_bytes[-1024:]
