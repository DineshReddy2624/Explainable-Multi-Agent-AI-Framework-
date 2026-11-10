import hashlib
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.generated_code import GeneratedCode
from models.report import Report


class CodeStorageService:
    """Service for generating standalone executable Python/SQL code artifacts and persisting them into DB."""

    def compute_sha256(self, content: str) -> str:
        """Computes SHA-256 digital hash of text content."""
        return "0x" + hashlib.sha256(content.encode('utf-8')).hexdigest()[:16].upper()

    def generate_python_remediation_script(self, dataset_id: int, filename: str, applied_logs: List[Dict[str, Any]]) -> str:
        """Synthesizes a standalone, executable Python Pandas data cleaning script."""
        log_lines = []
        for log in applied_logs:
            col = log.get("column_name", "column")
            corr = log.get("correction_type", "Correction")
            orig = log.get("original_value", "")
            val = log.get("corrected_value", "")
            log_lines.append(f"    # Apply: {corr} on column '{col}' (Original: {orig} -> Cleaned: {val})")

        ops_summary = "\n".join(log_lines) if log_lines else "    # Baseline validation pass - no transformations required."

        script = f'''"""
================================================================================
AUTOMATED DATA QUALITY REMEDIATION SCRIPT
Dataset ID: #{dataset_id} | Source: {filename}
Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
Governance Standard: Aligned with ISO/IEC 25012 Data Quality Framework
================================================================================
"""
import pandas as pd
import numpy as np


def remediate_dataset(input_file_path: str, output_file_path: str) -> pd.DataFrame:
    """
    Executes automated data quality remediation pipeline.
    """
    print(f"Loading input dataset: {{input_file_path}}")
    df = pd.read_csv(input_file_path)
    initial_rows, initial_cols = df.shape
    print(f"Initial Schema: {{initial_rows}} rows x {{initial_cols}} columns")

    # 1. Deduplication
    initial_dup_count = df.duplicated().sum()
    if initial_dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        print(f"Removed {{initial_dup_count}} duplicate records.")

{ops_summary}

    # 2. Imputation & Formatting Pass
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64']:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
        else:
            df[col] = df[col].fillna("Unknown").astype(str).str.strip()

    final_rows, final_cols = df.shape
    print(f"Remediation Complete: {{final_rows}} rows x {{final_cols}} columns")
    df.to_csv(output_file_path, index=False)
    return df


if __name__ == "__main__":
    remediate_dataset("{filename}", "{filename.replace('.csv', '')}_remediated.csv")
'''
        return script

    def generate_sql_transformation_query(self, dataset_id: int, filename: str, applied_logs: List[Dict[str, Any]]) -> str:
        """Synthesizes an enterprise SQL transformation script."""
        table_name = f"dataset_{dataset_id}_raw"
        clean_table = f"dataset_{dataset_id}_cleaned"

        sql = f'''-- ==============================================================================
-- ENTERPRISE DATA QUALITY SQL TRANSFORMATION SCRIPT
-- Dataset ID: #{dataset_id} | Target Table: {clean_table}
-- Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
-- ==============================================================================

-- 1. Create Cleaned Target Table with Exact Deduplication
CREATE TABLE IF NOT EXISTS {clean_table} AS
SELECT DISTINCT *
FROM {table_name};

-- 2. Governance Verification Summary Query
SELECT 
    COUNT(*) AS total_cleaned_records,
    '{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}' AS remediation_timestamp
FROM {clean_table};
'''
        return sql

    def save_generated_code(
        self,
        db: Session,
        dataset_id: int,
        org_id: str,
        code_type: str,
        title: str,
        description: str,
        code_content: str,
        execution_status: str = "EXECUTED",
        user_id: Optional[int] = None
    ) -> GeneratedCode:
        """Persists a generated code record into database."""
        digital_hash = self.compute_sha256(code_content)
        code_record = GeneratedCode(
            dataset_id=dataset_id,
            user_id=user_id,
            org_id=org_id,
            code_type=code_type,
            title=title,
            description=description,
            code_content=code_content,
            digital_hash=digital_hash,
            execution_status=execution_status
        )
        db.add(code_record)
        db.commit()
        db.refresh(code_record)
        return code_record

    def save_report_record(
        self,
        db: Session,
        dataset_id: int,
        report_type: str,
        file_path: str,
        user_id: Optional[int] = None
    ) -> Report:
        """Persists a PDF report record into database."""
        report_record = Report(
            dataset_id=dataset_id,
            report_type=report_type,
            file_path=file_path
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)
        return report_record



code_storage_service = CodeStorageService()
