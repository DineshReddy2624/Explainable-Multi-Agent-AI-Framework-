import sys
import os
import pytest
import pandas as pd

backend_dir = os.path.abspath("backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.agents.dynamic_remediator import DynamicDatasetRemediator

remediator = DynamicDatasetRemediator()


def test_pii_remediation_preserves_existing_and_sets_not_provided_for_missing():
    """Verify that apply_remediation preserves existing emails and phone numbers 100% as-is without formatting them or changing domains, and sets NOT_PROVIDED only for missing PII entries."""
    df = pd.DataFrame({
        "Full_Name": ["John Doe", None, "Alice Smith"],
        "Customer_Email": ["julia.johnson@enterprise.org", "invalid_email_no_domain", None],
        "Phone_Number": ["(664) 750-6977", "1234567890", None],
        "Monthly_Salary": [5000.0, -2000.0, None]
    })

    cleaned_df, logs = remediator.apply_remediation(df, cell_edits=[], strategies=[], auto_remediate_all=True)

    # 1. Existing valid Email check: Must stay EXACTLY 'julia.johnson@enterprise.org' (not changed to .com!)
    email_at_row0 = cleaned_df.at[0, "Customer_Email"]
    assert email_at_row0 == "julia.johnson@enterprise.org"

    # 2. Existing invalid/unparseable Email check: Preserved as-is
    email_at_row1 = cleaned_df.at[1, "Customer_Email"]
    assert email_at_row1 == "invalid_email_no_domain"

    # 3. Missing Email check: Set to 'NOT_PROVIDED'
    email_at_row2 = cleaned_df.at[2, "Customer_Email"]
    assert email_at_row2 == "NOT_PROVIDED"

    # 4. Existing Phone check: Preserved EXACTLY as-is without reformatting
    phone_at_row0 = cleaned_df.at[0, "Phone_Number"]
    phone_at_row1 = cleaned_df.at[1, "Phone_Number"]
    assert phone_at_row0 == "(664) 750-6977"
    assert phone_at_row1 == "1234567890"

    # 5. Missing Phone check: Set to 'NOT_PROVIDED'
    phone_at_row2 = cleaned_df.at[2, "Phone_Number"]
    assert phone_at_row2 == "NOT_PROVIDED"

    # 6. Non-PII Salary check: Negative salary MUST be corrected using abs()
    salary_at_row1 = cleaned_df.at[1, "Monthly_Salary"]
    assert salary_at_row1 == 2000.0
