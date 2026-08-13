import re
import pandas as pd
import numpy as np

class DynamicDatasetRemediator:
    def __init__(self):
        self.email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        self.phone_regex = r'^\+?[1-9]\d{1,14}$|^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$'

    def apply_remediation(self, df: pd.DataFrame, cell_edits: list, strategies: list, auto_remediate_all: bool = False) -> tuple:
        cleaned_df = df.copy()
        remediation_logs = []
        original_df = df.copy()

        # Build column strategy lookup map
        strat_map = {s.get("col"): s for s in strategies if s.get("col")}

        # 1. Apply manual / single cell edits
        for edit in cell_edits:
            row_idx = edit.get("row")
            col_name = edit.get("col")
            val = edit.get("val")
            if row_idx is not None and col_name in cleaned_df.columns and 0 <= row_idx < len(cleaned_df):
                orig_val = original_df.at[row_idx, col_name]
                try:
                    if str(val).replace('.', '', 1).isdigit():
                        val = float(val) if '.' in str(val) else int(val)
                except Exception:
                    pass
                cleaned_df.at[row_idx, col_name] = val
                remediation_logs.append({
                    "row_index": row_idx,
                    "column_name": col_name,
                    "original_value": str(orig_val) if pd.notnull(orig_val) else "[NULL]",
                    "corrected_value": str(val),
                    "correction_type": "User / Single Cell Fix",
                    "applied_by": "User",
                    "confidence_score": 1.0,
                    "status": "Applied ✓"
                })

        # 2. Process column strategies
        headers = list(cleaned_df.columns)
        numeric_cols = list(cleaned_df.select_dtypes(include=[np.number]).columns)

        for col in headers:
            strat_info = strat_map.get(col, {})
            action = strat_info.get("strategy")
            custom_val = strat_info.get("custom_val")

            if action == "KEEP_ORIGINAL":
                continue

            if action == "DROP_COLUMN":
                cleaned_df = cleaned_df.drop(columns=[col])
                continue

            if action == "DROP_DUPLICATES":
                cleaned_df = cleaned_df.drop_duplicates()
                continue

            # Only auto-impute if explicit strategy is provided OR auto_remediate_all is True
            should_impute = (action is not None and action != "KEEP_ORIGINAL") or auto_remediate_all

            if should_impute:
                null_mask = cleaned_df[col].isnull() | (cleaned_df[col].astype(str).str.strip() == "") | (cleaned_df[col].astype(str).str.lower() == "nan")
                null_indices = list(cleaned_df[null_mask].index)

                if len(null_indices) > 0:
                    if action == "FILL_MEAN" and col in numeric_cols:
                        rep_val = round(float(cleaned_df[col].dropna().mean()), 2)
                        c_type = "Mean Imputation"
                    elif action == "FILL_MEDIAN" or (auto_remediate_all and col in numeric_cols):
                        non_nulls = cleaned_df[col].dropna()
                        rep_val = round(float(non_nulls.median()), 2) if not non_nulls.empty else 0.0
                        c_type = "Median Imputation"
                    elif action == "FILL_MODE" or (auto_remediate_all and col not in numeric_cols):
                        modes = cleaned_df[col].dropna().mode()
                        rep_val = str(modes.iloc[0]) if not modes.empty else "N/A"
                        c_type = "Mode Imputation"
                    elif action == "FILL_CUSTOM" and custom_val is not None:
                        rep_val = custom_val
                        c_type = "Custom Imputation"
                    else:
                        rep_val = "N/A"
                        c_type = "AI Imputation"

                    # Apply imputation to missing cells
                    cleaned_df[col] = cleaned_df[col].fillna(rep_val)
                    cleaned_df.loc[null_mask, col] = rep_val

                    for idx in null_indices:
                        orig_val = original_df.at[idx, col] if idx in original_df.index else "[NULL]"
                        remediation_logs.append({
                            "row_index": idx,
                            "column_name": col,
                            "original_value": str(orig_val) if pd.notnull(orig_val) and str(orig_val).strip() != "" else "[NULL]",
                            "corrected_value": str(rep_val),
                            "correction_type": c_type,
                            "applied_by": "AI Agent",
                            "confidence_score": 0.95,
                            "status": "Applied ✓"
                        })

        # 3. Automatic Format Cleaning for Email / Phone (only during full auto-remediation)
        if auto_remediate_all:
            for col in headers:
                if col in cleaned_df.columns:
                    col_lower = col.lower()
                    if "email" in col_lower:
                        for idx, val in cleaned_df[col].items():
                            val_str = str(val).strip()
                            if val_str and val_str != "[NULL]" and not re.match(self.email_regex, val_str):
                                clean_email = val_str.lower().replace(" ", "") if "@" in val_str else f"{val_str}@example.com"
                                cleaned_df.at[idx, col] = clean_email
                                remediation_logs.append({
                                    "row_index": idx,
                                    "column_name": col,
                                    "original_value": val_str,
                                    "corrected_value": clean_email,
                                    "correction_type": "Regex Format Normalization",
                                    "applied_by": "AI Agent",
                                    "confidence_score": 0.98,
                                    "status": "Applied ✓"
                                })

        return cleaned_df, remediation_logs
