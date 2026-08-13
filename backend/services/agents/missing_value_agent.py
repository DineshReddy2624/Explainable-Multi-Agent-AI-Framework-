import pandas as pd

class MissingValueAgent:
    def __init__(self):
        self.name = "Missing Value Agent"

    def execute(self, df: pd.DataFrame) -> dict:
        total_rows = len(df)
        missing_report = {}
        suggestions = []

        for col in df.columns:
            # Check for null, NaN, empty strings
            null_mask = df[col].isnull() | (df[col].astype(str).str.strip() == "") | (df[col].astype(str).str.lower() == "nan")
            null_count = int(null_mask.sum())
            missing_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

            if null_count > 0:
                missing_report[col] = {
                    "null_count": null_count,
                    "missing_pct": missing_pct
                }

                # Generate remediation suggestion
                if pd.api.types.is_numeric_dtype(df[col]):
                    rec_action = "IMPUTE_MEDIAN"
                    rec_val = float(df[col].median()) if not df[col].isnull().all() else 0
                else:
                    rec_action = "IMPUTE_MODE"
                    mode_val = df[col].mode()
                    rec_val = str(mode_val[0]) if not mode_val.empty else "N/A"

                suggestions.append({
                    "column": col,
                    "issue": "MISSING_VALUE",
                    "missing_count": null_count,
                    "missing_pct": missing_pct,
                    "suggested_action": rec_action,
                    "suggested_value": rec_val
                })

        return {
            "agent": self.name,
            "missing_report": missing_report,
            "suggestions": suggestions
        }
