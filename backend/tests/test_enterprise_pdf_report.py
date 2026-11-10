import sys
import os
import pytest
import pandas as pd
import numpy as np

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath("backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.agents.dynamic_analyzer import DynamicDatasetAnalyzer
from services.agents.dynamic_remediator import DynamicDatasetRemediator
from services.reports.report_services import (
    DatasetProfileService,
    QualityAssessmentService,
    MissingValueAnalysisService,
    DuplicateAnalysisService,
    FormatValidationService,
    AnomalyAnalysisService,
    RemediationSummaryService,
    BeforeAfterComparisonService,
    AuditTrailService,
    ReportValidationService
)
from services.reports.chart_generator import ChartGenerationService
from services.exporter.pdf_report import generate_before_after_pdf_bytes


@pytest.fixture
def analyzer():
    return DynamicDatasetAnalyzer()


@pytest.fixture
def remediator():
    return DynamicDatasetRemediator()


def test_clean_dataset_profiling_and_report(analyzer):
    """Verify that a 100% clean dataset generates an optimal profile with zero defects."""
    df_clean = pd.DataFrame({
        "Customer_ID": [101, 102, 103, 104, 105],
        "Age": [25, 34, 45, 52, 61],
        "Email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com", "eva@example.com"],
        "Salary": [55000.0, 65000.0, 75000.0, 85000.0, 95000.0]
    })

    analysis = analyzer.analyze(df_clean, filename="clean_dataset.csv")

    assert analysis["total_rows"] == 5
    assert analysis["total_cols"] == 4
    assert analysis["total_missing_cells"] == 0
    assert analysis["duplicate_count"] == 0
    assert len(analysis["format_issues"]) == 0
    assert analysis["quality_scores"]["overall_score"] >= 95.0

    pdf_bytes = generate_before_after_pdf_bytes(
        before_analysis=analysis,
        after_analysis=analysis,
        applied_logs=[],
        filename="clean_dataset.csv",
        dataset_id=99,
        org_id="test_org"
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF-")


def test_dirty_dataset_remediation_and_pdf_generation(analyzer, remediator):
    """Verify analysis, remediation, reconciliation, and PDF generation on a dirty dataset."""
    df_dirty = pd.DataFrame({
        "Customer_ID": [101, 102, 103, 104, 105, 105],  # 1 duplicate
        "Age": [25, -5.0, np.nan, 45, 150.0, 150.0],    # Missing & Range errors
        "Email": ["user1@example.com", "bad email", np.nan, "user4@example.com", "user5@example.com", "user5@example.com"], # Format & Missing
        "Phone": ["5551234567", "555-1234", "555-999-0000", "5550001111", "5552223333", "5552223333"], # Non-standard
        "Salary": [50000.0, -1000.0, 75000.0, 1250000.0, 85000.0, 85000.0] # Negative & Outlier
    })

    before_analysis = analyzer.analyze(df_dirty, filename="dirty_dataset.csv")
    df_cleaned, logs = remediator.apply_remediation(df_dirty, cell_edits=[], strategies=[], auto_remediate_all=True)
    after_analysis = analyzer.analyze(df_cleaned, filename="dirty_cleaned.csv")

    assert before_analysis["total_rows"] == 6
    assert after_analysis["total_rows"] == 5  # Deduplicated
    assert after_analysis["total_missing_cells"] == 0
    assert after_analysis["duplicate_count"] == 0

    # Test Data Reconciliation Service
    val_service = ReportValidationService()
    reconcil = val_service.validate_reconciliation(before_analysis, after_analysis, logs)
    assert reconcil["is_valid"] is True

    # Test PDF generation
    pdf_bytes = generate_before_after_pdf_bytes(
        before_analysis=before_analysis,
        after_analysis=after_analysis,
        applied_logs=logs,
        filename="dirty_dataset.csv",
        dataset_id=101,
        org_id="test_org"
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF-")


def test_chart_generation_service():
    """Verify that ChartGenerationService produces valid PNG image bytes."""
    chart_service = ChartGenerationService()

    b1 = chart_service.generate_quality_comparison_chart(85.0, 99.5)
    assert isinstance(b1, bytes)
    assert b1.startswith(b"\x89PNG")

    dims = [
        {"name": "Completeness", "before": 80.0, "after": 100.0},
        {"name": "Uniqueness", "before": 90.0, "after": 100.0},
        {"name": "Validity", "before": 75.0, "after": 100.0},
        {"name": "Consistency", "before": 85.0, "after": 99.5},
        {"name": "Accuracy", "before": 95.0, "after": 95.0}
    ]
    b2 = chart_service.generate_dimension_radar_chart(dims)
    assert isinstance(b2, bytes)
    assert b2.startswith(b"\x89PNG")

    b3 = chart_service.generate_issue_reduction_chart(100, 0, 10, 0, 50, 0, 5, 1)
    assert isinstance(b3, bytes)
    assert b3.startswith(b"\x89PNG")


def test_reconciliation_validation_failure_detection():
    """Verify that ReportValidationService correctly flags metric reconciliation discrepancies."""
    val_service = ReportValidationService()

    before_mock = {"total_rows": 100, "duplicate_count": 10, "total_missing_cells": 50, "quality_scores": {"overall_score": 80.0}}
    # Mock inconsistent after state: claiming 105 rows after 10 duplicate removals
    after_mock_inconsistent = {"total_rows": 105, "duplicate_count": 0, "total_missing_cells": 0, "quality_scores": {"overall_score": 95.0}}

    res = val_service.validate_reconciliation(before_mock, after_mock_inconsistent, logs=[{"col": "x"}])
    assert res["is_valid"] is False
    assert len(res["discrepancies"]) > 0
    assert "Row count discrepancy" in res["discrepancies"][0]
