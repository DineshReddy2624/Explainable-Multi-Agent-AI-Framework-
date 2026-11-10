import os
import sqlite3
import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database", "data_quality.db"))
print(f"Connecting to database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Inspect existing columns
cursor.execute("PRAGMA table_info(uploaded_datasets);")
columns = [row[1] for row in cursor.fetchall()]
print(f"Current columns in uploaded_datasets: {columns}")

# 2. Add columns if not present
new_columns = [
    ("source_type", "VARCHAR DEFAULT 'USER_UPLOAD'"),
    ("artifact_type", "VARCHAR DEFAULT 'RAW_DATASET'"),
    ("is_persisted", "BOOLEAN DEFAULT 0"),
    ("cleaned_filename", "VARCHAR DEFAULT NULL"),
]

for col_name, col_def in new_columns:
    if col_name not in columns:
        print(f"Adding column '{col_name}' to uploaded_datasets...")
        cursor.execute(f"ALTER TABLE uploaded_datasets ADD COLUMN {col_name} {col_def};")
    else:
        print(f"Column '{col_name}' already exists.")

conn.commit()

# 3. Identify all datasets that have an actual saved workflow bundle in dataset_metadata
cursor.execute("""
    SELECT d.id, d.filename, d.status, m.saved_at
    FROM uploaded_datasets d
    JOIN dataset_metadata m ON d.id = m.dataset_id
    WHERE m.workflow_bundle IS NOT NULL AND m.saved_at IS NOT NULL
""")
persisted_datasets = cursor.fetchall()
print(f"\nFound {len(persisted_datasets)} genuinely persisted datasets with workflow bundles:")
for p in persisted_datasets:
    print(f"  -> ID: {p[0]}, Filename: {p[1]}, Status: {p[2]}, Saved At: {p[3]}")

# 4. Migrate genuinely persisted datasets
persisted_ids = [p[0] for p in persisted_datasets]
for ds_id in persisted_ids:
    cursor.execute("SELECT filename FROM uploaded_datasets WHERE id = ?", (ds_id,))
    fn = cursor.fetchone()[0]
    cleaned_fn = f"cleaned_dataset_{ds_id}.csv"
    cursor.execute("""
        UPDATE uploaded_datasets
        SET is_persisted = 1,
            artifact_type = 'CLEANED_DATASET',
            source_type = 'CLEANED_DATASET',
            status = 'SAVED',
            version_type = 'SAVED',
            cleaned_filename = ?
        WHERE id = ?
    """, (cleaned_fn, ds_id))

# 5. Classify and update all other datasets (raw uploads, test tasks, demo parquet/csv files)
# These must NOT be marked as is_persisted = 1!
if persisted_ids:
    placeholders = ",".join("?" for _ in persisted_ids)
    cursor.execute(f"""
        UPDATE uploaded_datasets
        SET is_persisted = 0,
            artifact_type = 'RAW_DATASET'
        WHERE id NOT IN ({placeholders})
    """, persisted_ids)
else:
    cursor.execute("""
        UPDATE uploaded_datasets
        SET is_persisted = 0,
            artifact_type = 'RAW_DATASET'
    """)

# Reset any spurious 'SAVED' status for datasets without a workflow bundle
cursor.execute("""
    UPDATE uploaded_datasets
    SET status = 'CLEANED'
    WHERE status = 'SAVED' AND id NOT IN (
        SELECT dataset_id FROM dataset_metadata WHERE workflow_bundle IS NOT NULL
    )
""")

# Classify demo/sample datasets
demo_keywords = [
    "dataset_1", "dataset_2", "dataset_3", "dataset_4", "dataset_5",
    "dataset_6", "dataset_7", "dataset_8", "dataset_9", "dataset_10",
    "dataset_11", "dataset_12", "dataset_13", "dataset_14", "dataset_15",
    "dataset_16", "customer_demographics", "e_commerce_transactions",
    "healthcare_patient", "financial_loan", "hr_employee", "iot_sensor",
    "customer_churn", "real_estate", "cybersecurity_audit", "credit_card_fraud",
    "synthetic_employees", "customer_pii", "benchmark_employees", "test_task"
]

cursor.execute("SELECT id, filename FROM uploaded_datasets WHERE is_persisted = 0")
non_persisted = cursor.fetchall()
demo_count = 0
for row_id, fn in non_persisted:
    fn_lower = (fn or "").lower()
    is_demo = any(k in fn_lower for k in demo_keywords)
    st = "DEMO" if is_demo else "USER_UPLOAD"
    if is_demo:
        demo_count += 1
    cursor.execute("UPDATE uploaded_datasets SET source_type = ? WHERE id = ?", (st, row_id))

conn.commit()

# 6. Verification counts
cursor.execute("SELECT COUNT(*) FROM uploaded_datasets WHERE is_persisted = 1 AND artifact_type = 'CLEANED_DATASET'")
saved_repo_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM uploaded_datasets WHERE is_persisted = 0")
unpersisted_count = cursor.fetchone()[0]

cursor.execute("SELECT source_type, COUNT(*) FROM uploaded_datasets GROUP BY source_type")
source_breakdown = cursor.fetchall()

print("\n" + "=" * 50)
print("MIGRATION COMPLETED SUCCESSFULLY")
print("=" * 50)
print(f"Eligible Saved Repository Datasets (is_persisted=1, artifact_type='CLEANED_DATASET'): {saved_repo_count}")
print(f"Unpersisted Source/Working Datasets (is_persisted=0, artifact_type='RAW_DATASET')   : {unpersisted_count}")
print(f"Source Type Breakdown: {source_breakdown}")
print("=" * 50)

conn.close()
