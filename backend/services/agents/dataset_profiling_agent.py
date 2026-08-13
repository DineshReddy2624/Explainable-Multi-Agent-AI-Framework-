import pandas as pd
import numpy as np

class DatasetProfilingAgent:
    def __init__(self):
        self.name = "Dataset Profiling Agent"

    def execute(self, df: pd.DataFrame) -> dict:
        total_rows = len(df)
        total_cols = len(df.columns)
        col_names = list(df.columns)

        datatype_map = {}
        for col in col_names:
            datatype_map[col] = str(df[col].dtype)

        stats_summary = {}
        for col in col_names:
            if pd.api.types.is_numeric_dtype(df[col]):
                stats_summary[col] = {
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else 0,
                    "median": float(df[col].median()) if not df[col].isnull().all() else 0,
                    "std": float(df[col].std()) if not df[col].isnull().all() else 0,
                    "min": float(df[col].min()) if not df[col].isnull().all() else 0,
                    "max": float(df[col].max()) if not df[col].isnull().all() else 0,
                }

        return {
            "agent": self.name,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "column_names": col_names,
            "datatype_map": datatype_map,
            "stats_summary": stats_summary
        }
