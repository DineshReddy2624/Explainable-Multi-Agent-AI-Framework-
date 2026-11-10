import re
import pandas as pd
import numpy as np
from services.privacy.pii_detector import pii_detector

PII_KEYWORDS = [
    "name", "full_name", "first_name", "last_name", "firstname", "lastname", "surname",
    "email", "phone", "mobile", "cell", "telephone", "address", "street", "zip", "postal",
    "ssn", "social_security", "tax_id", "passport", "dob", "birth", "date_of_birth",
    "gender", "sex", "credit_card", "card_number", "customer_name", "employee_name",
    "user_name", "username", "owner_name", "contact_name"
]


class DynamicDatasetRemediator:
    def __init__(self):
        self.email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        self.phone_regex = r'^\+?[1-9]\d{1,14}$|^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$'

    def is_pii_column(self, col_name: str, pii_detected_set: set) -> bool:
        if not col_name:
            return False
        if col_name in pii_detected_set:
            return True
        c_lower = str(col_name).lower().strip()
        return any(kw in c_lower for kw in PII_KEYWORDS)

    def apply_remediation(self, df: pd.DataFrame, cell_edits: list, strategies: list, auto_remediate_all: bool = False) -> tuple:
        cleaned_df = df.copy()
        remediation_logs = []
        original_df = df.copy()

        # Identify all PII columns upfront to protect personal data
        detected_pii = pii_detector.detect_pii_columns(cleaned_df)
        pii_cols_set = {item["column"] for item in detected_pii}

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

        # 2. Process column strategies & Imputations
        headers = list(cleaned_df.columns)

        def is_numeric_col(column):
            s = cleaned_df[column].dropna()
            if s.empty:
                return False
            converted = pd.to_numeric(s, errors='coerce')
            return converted.notnull().sum() / len(s) > 0.5

        for col in headers:
            if col not in cleaned_df.columns:
                continue

            # Check if this column contains Personal Identifiable Information (PII)
            is_pii = self.is_pii_column(col, pii_cols_set)

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

            # STRICT PII POLICY: Use NOT_PROVIDED for missing PII data (No random fake data generated!)
            if is_pii and (action == "FILL_MODE" or auto_remediate_all):
                null_mask = cleaned_df[col].isnull() | (cleaned_df[col].astype(str).str.strip() == "") | (cleaned_df[col].astype(str).str.lower() == "nan")
                null_indices = list(cleaned_df[null_mask].index)
                cleaned_df.loc[null_mask, col] = "NOT_PROVIDED"
                for idx in null_indices:
                    orig_val = original_df.at[idx, col] if idx in original_df.index else "[NULL]"
                    remediation_logs.append({
                        "row_index": idx,
                        "column_name": col,
                        "original_value": str(orig_val) if pd.notnull(orig_val) and str(orig_val).strip() != "" else "[NULL]",
                        "corrected_value": "NOT_PROVIDED",
                        "correction_type": "PII Protection: NOT_PROVIDED Placeholder",
                        "applied_by": "PII Policy Engine",
                        "confidence_score": 1.0,
                        "status": "Applied ✓"
                    })
                continue

            should_impute = (action is not None and action != "KEEP_ORIGINAL") or auto_remediate_all

            if should_impute:
                null_mask = cleaned_df[col].isnull() | (cleaned_df[col].astype(str).str.strip() == "") | (cleaned_df[col].astype(str).str.lower() == "nan")
                null_indices = list(cleaned_df[null_mask].index)

                if len(null_indices) > 0:
                    is_num = is_numeric_col(col)
                    if is_num:
                        clean_numeric_series = pd.to_numeric(cleaned_df[col].dropna(), errors='coerce').dropna()

                    if is_pii:
                        rep_val = "NOT_PROVIDED"
                        c_type = "PII Placeholder (NOT_PROVIDED)"
                    elif action == "FILL_MEAN" and is_num:
                        rep_val = round(float(clean_numeric_series.mean()), 2) if not clean_numeric_series.empty else 0.0
                        c_type = "Mean Imputation"
                    elif action == "FILL_MEDIAN" or (auto_remediate_all and is_num):
                        rep_val = round(float(clean_numeric_series.median()), 2) if not clean_numeric_series.empty else 0.0
                        c_type = "Median Imputation"
                    elif action == "FILL_MODE" or (auto_remediate_all and not is_num):
                        modes = cleaned_df[col].dropna().mode()
                        rep_val = str(modes.iloc[0]) if not modes.empty else "N/A"
                        c_type = "Mode Imputation"
                    elif action == "FILL_CUSTOM" and custom_val is not None:
                        rep_val = custom_val
                        c_type = "Custom Imputation"
                    else:
                        rep_val = "N/A"
                        c_type = "AI Imputation"

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

        # 3. Format Normalization (Age, Email, Phone, Currency, Date) during auto-remediation
        if auto_remediate_all:
            for col in list(cleaned_df.columns):
                col_lower = col.lower()
                is_pii = self.is_pii_column(col, pii_cols_set)

                # A. Age Column Remediation (Range [0, 120])
                if "age" in col_lower:
                    numeric_ages = pd.to_numeric(cleaned_df[col], errors='coerce')
                    valid_mask = (numeric_ages >= 0) & (numeric_ages <= 120)
                    valid_ages = numeric_ages[valid_mask]
                    median_age = round(float(valid_ages.median()), 1) if not valid_ages.empty else 35.0

                    for idx, val in cleaned_df[col].items():
                        num = numeric_ages.at[idx]
                        if pd.isna(num) or num < 0 or num > 120:
                            cleaned_df.at[idx, col] = median_age
                            remediation_logs.append({
                                "row_index": idx,
                                "column_name": col,
                                "original_value": str(val),
                                "corrected_value": str(median_age),
                                "correction_type": "Age Format & Range Normalization",
                                "applied_by": "AI Agent",
                                "confidence_score": 0.98,
                                "status": "Applied ✓"
                            })

                # B. Email Column (DO NOT alter or format existing emails; only fill missing with NOT_PROVIDED)
                elif "email" in col_lower:
                    for idx, val in cleaned_df[col].items():
                        val_str = str(val).strip() if pd.notnull(val) else ""
                        if not val_str or val_str.lower() in ["nan", "null", "none", "[null]"]:
                            cleaned_df.at[idx, col] = "NOT_PROVIDED"
                            remediation_logs.append({
                                "row_index": idx,
                                "column_name": col,
                                "original_value": val_str if val_str else "[NULL]",
                                "corrected_value": "NOT_PROVIDED",
                                "correction_type": "Email PII Placeholder",
                                "applied_by": "AI Agent",
                                "confidence_score": 1.0,
                                "status": "Applied ✓"
                            })
                        # Present emails are left 100% untouched as-is (no regex alterations or fake domain changes)

                # C. Phone Column (DO NOT reformat existing phone numbers; only fill missing with NOT_PROVIDED)
                elif "phone" in col_lower or "mobile" in col_lower:
                    for idx, val in cleaned_df[col].items():
                        val_str = str(val).strip() if pd.notnull(val) else ""
                        if not val_str or val_str.lower() in ["nan", "null", "none", "[null]"]:
                            cleaned_df.at[idx, col] = "NOT_PROVIDED"
                            remediation_logs.append({
                                "row_index": idx,
                                "column_name": col,
                                "original_value": val_str if val_str else "[NULL]",
                                "corrected_value": "NOT_PROVIDED",
                                "correction_type": "Phone PII Placeholder",
                                "applied_by": "AI Agent",
                                "confidence_score": 1.0,
                                "status": "Applied ✓"
                            })
                        # Present phone numbers are left 100% untouched as-is (no formatting or digit alterations)




                # D. Currency / Financial Sign & Format Correction
                elif any(k in col_lower for k in ["salary", "income", "price", "amount", "revenue", "cost", "fee"]):
                    numeric_vals = pd.to_numeric(cleaned_df[col], errors='coerce')
                    valid_positives = numeric_vals[numeric_vals > 0]
                    median_pos = round(float(valid_positives.median()), 2) if not valid_positives.empty else 50000.0

                    for idx, val in cleaned_df[col].items():
                        num = numeric_vals.at[idx]
                        if pd.notna(num) and num < 0:
                            clean_val = round(abs(float(num)), 2)
                            cleaned_df.at[idx, col] = clean_val
                            remediation_logs.append({
                                "row_index": idx,
                                "column_name": col,
                                "original_value": str(val),
                                "corrected_value": str(clean_val),
                                "correction_type": "Currency Sign Correction",
                                "applied_by": "AI Agent",
                                "confidence_score": 0.99,
                                "status": "Applied ✓"
                            })

        # 4. ML Outliers Remediation (IQR & Percentile Bounding across all numeric columns)
        if auto_remediate_all:
            for col in cleaned_df.columns:
                if any(id_k in col.lower() for id_k in ["id", "key", "index"]):
                    continue

                # Coerce to numeric to catch object-typed numeric columns
                clean_s = pd.to_numeric(
                    cleaned_df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip(),
                    errors='coerce'
                )

                valid_count = int(clean_s.dropna().count())
                if valid_count > 5 and (pd.api.types.is_numeric_dtype(cleaned_df[col]) or valid_count / len(cleaned_df) > 0.5):
                    s = clean_s.dropna()
                    q1 = float(s.quantile(0.25))
                    q3 = float(s.quantile(0.75))
                    iqr = q3 - q1
                    
                    if iqr > 0:
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr

                        # Domain rules protection
                        if "credit" in col.lower() or "score" in col.lower():
                            lower_bound = max(350.0, lower_bound)
                            upper_bound = min(850.0, upper_bound)

                        outlier_mask = (clean_s < lower_bound) | (clean_s > upper_bound)
                        outlier_indices = list(cleaned_df[outlier_mask].index)

                        for idx in outlier_indices:
                            orig_val = cleaned_df.at[idx, col]
                            curr_num = clean_s.at[idx]
                            if pd.notna(curr_num):
                                bounded_val = round(float(np.clip(curr_num, lower_bound, upper_bound)), 2)
                                cleaned_df.at[idx, col] = bounded_val
                                remediation_logs.append({
                                    "row_index": idx,
                                    "column_name": col,
                                    "original_value": str(orig_val),
                                    "corrected_value": str(bounded_val),
                                    "correction_type": "ML Outlier IQR Bounding",
                                    "applied_by": "AI Agent",
                                    "confidence_score": 0.95,
                                    "status": "Applied ✓"
                                })

        # 5. Duplicate Rows Cleanup
        if auto_remediate_all and cleaned_df.duplicated().sum() > 0:
            dup_count = int(cleaned_df.duplicated().sum())
            cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
            remediation_logs.append({
                "row_index": 0,
                "column_name": "Dataset",
                "original_value": f"{dup_count} duplicate rows",
                "corrected_value": "0 duplicate rows",
                "correction_type": "Duplicate Rows Deduplication",
                "applied_by": "AI Agent",
                "confidence_score": 1.0,
                "status": "Applied ✓"
            })

        return cleaned_df, remediation_logs

