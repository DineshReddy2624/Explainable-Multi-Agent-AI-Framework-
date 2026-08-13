import pandas as pd

class IntelligentAutoCorrectionAgent:
    def __init__(self):
        self.name = "Intelligent Auto Correction Agent"

    def execute(self, df: pd.DataFrame, missing_suggs: list, dup_suggs: str) -> dict:
        corrections = []

        # Process Missing Suggestions
        for sugg in missing_suggs:
            col = sugg["column"]
            action = sugg["suggested_action"]
            corrections.append({
                "column_name": col,
                "issue_type": "MISSING_VALUE",
                "recommended_action": action,
                "confidence_score": 0.95 if action == "IMPUTE_MEDIAN" else 0.88,
                "status": "RECOMMENDED"
            })

        # Process Duplicate Suggestions
        if dup_suggs == "KEEP_FIRST_RECORD":
            corrections.append({
                "column_name": "ROW_LEVEL",
                "issue_type": "DUPLICATE_ROWS",
                "recommended_action": "DROP_DUPLICATES",
                "confidence_score": 0.99,
                "status": "RECOMMENDED"
            })

        return {
            "agent": self.name,
            "corrections": corrections
        }

    def apply_corrections(self, df: pd.DataFrame, approved_corrections: list) -> pd.DataFrame:
        cleaned_df = df.copy()
        for corr in approved_corrections:
            col = corr.get("column_name")
            action = corr.get("recommended_action")

            if action == "IMPUTE_MEDIAN" and col in cleaned_df.columns:
                med_val = cleaned_df[col].median()
                cleaned_df[col] = cleaned_df[col].fillna(med_val)
            elif action == "IMPUTE_MODE" and col in cleaned_df.columns:
                mode_val = cleaned_df[col].mode()
                if not mode_val.empty:
                    cleaned_df[col] = cleaned_df[col].fillna(mode_val[0])
            elif action == "DROP_DUPLICATES":
                cleaned_df = cleaned_df.drop_duplicates()

        return cleaned_df
