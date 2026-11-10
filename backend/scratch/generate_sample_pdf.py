import sys
import os
import pandas as pd

backend_dir = os.path.abspath("backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.agents.dynamic_analyzer import DynamicDatasetAnalyzer
from services.agents.dynamic_remediator import DynamicDatasetRemediator
from services.exporter.pdf_report import generate_before_after_pdf_bytes

raw_path = "datasets/original/1_customer_demographics_raw.csv"
df_before = pd.read_csv(raw_path)

analyzer = DynamicDatasetAnalyzer()
remediator = DynamicDatasetRemediator()

before_analysis = analyzer.analyze(df_before, filename="1_customer_demographics_raw.csv")
df_cleaned, logs = remediator.apply_remediation(df_before, cell_edits=[], strategies=[], auto_remediate_all=True)
after_analysis = analyzer.analyze(df_cleaned, filename="1_customer_demographics_cleaned.csv")

pdf_bytes = generate_before_after_pdf_bytes(
    before_analysis=before_analysis,
    after_analysis=after_analysis,
    applied_logs=logs,
    filename="1_customer_demographics_raw.csv",
    dataset_id=678,
    org_id="org_default"
)

output_pdf_path = "C:/Users/dines/.gemini/antigravity-ide/brain/e0fff471-2a73-48bf-877c-e4be00096a7e/sample_enterprise_data_quality_report.pdf"
with open(output_pdf_path, "wb") as f:
    f.write(pdf_bytes)

print(f"Successfully generated sample PDF report ({len(pdf_bytes):,} bytes) at: {output_pdf_path}")
