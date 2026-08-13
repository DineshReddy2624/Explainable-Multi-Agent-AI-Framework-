import pandas as pd

class DuplicateDetectionAgent:
    def __init__(self):
        self.name = "Duplicate Detection Agent"

    def execute(self, df: pd.DataFrame) -> dict:
        total_rows = len(df)
        duplicate_rows_count = int(df.duplicated().sum())

        column_duplicates = {}
        for col in df.columns:
            if "id" in col.lower() or "email" in col.lower() or "phone" in col.lower():
                dup_cnt = int(df[col].duplicated().sum())
                if dup_cnt > 0:
                    column_duplicates[col] = dup_cnt

        return {
            "agent": self.name,
            "duplicate_rows_count": duplicate_rows_count,
            "column_duplicates": column_duplicates,
            "suggested_action": "KEEP_FIRST_RECORD" if duplicate_rows_count > 0 else "NO_ACTION"
        }
