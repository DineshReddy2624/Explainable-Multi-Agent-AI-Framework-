import re
import pandas as pd

class FormatValidationAgent:
    def __init__(self):
        self.name = "Format Validation Agent"
        self.email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        self.phone_regex = r'^\+?[1-9]\d{1,14}$|^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$'

    def execute(self, df: pd.DataFrame) -> dict:
        format_issues = []

        for col in df.columns:
            col_lower = col.lower()
            if "email" in col_lower:
                invalid_count = 0
                for val in df[col].dropna():
                    if not re.match(self.email_regex, str(val).strip()):
                        invalid_count += 1
                if invalid_count > 0:
                    format_issues.append({
                        "column": col,
                        "expected_format": "EMAIL_PATTERN",
                        "invalid_count": invalid_count,
                        "suggested_action": "REGEX_CLEAN"
                    })
            elif "phone" in col_lower:
                invalid_count = 0
                for val in df[col].dropna():
                    if not re.match(self.phone_regex, str(val).strip()):
                        invalid_count += 1
                if invalid_count > 0:
                    format_issues.append({
                        "column": col,
                        "expected_format": "PHONE_PATTERN",
                        "invalid_count": invalid_count,
                        "suggested_action": "NORMALIZE_PHONE"
                    })

        return {
            "agent": self.name,
            "format_issues": format_issues
        }
