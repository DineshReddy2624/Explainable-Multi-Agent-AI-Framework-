import re
import pandas as pd
from typing import List, Dict, Any, Optional

# Regex Patterns for Value Signals
PATTERNS = {
    "EMAIL": re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'),
    "PHONE": re.compile(r'^\+?[0-9]{1,4}?[-. ]?\(?[0-9]{1,3}?\)?[-. ]?[0-9]{3,4}[-. ]?[0-9]{3,4}$'),
    "CREDIT_CARD": re.compile(r'^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})$'),
    "GOVERNMENT_ID": re.compile(r'^\d{3}-\d{2}-\d{4}$'),  # SSN format
    "IP_ADDRESS": re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'),
}

COLUMN_NAME_SIGNALS = {
    "EMAIL": ["email", "e_mail", "mail", "user_email"],
    "PHONE": ["phone", "mobile", "cell", "telephone", "phone_number"],
    "CREDIT_CARD": ["card", "credit_card", "card_number", "cc_num", "cvv"],
    "PERSON_NAME": ["name", "full_name", "first_name", "last_name", "patient_name", "customer_name", "author"],
    "GOVERNMENT_ID": ["ssn", "tax_id", "govt_id", "national_id", "social_security"],
    "PASSPORT": ["passport", "passport_num", "passport_no"],
    "ADDRESS": ["address", "street", "city", "location", "residence"],
    "POSTAL_CODE": ["zip", "zipcode", "postal_code", "postcode"],
    "DATE_OF_BIRTH": ["dob", "birth_date", "birthday", "date_of_birth"],
    "BANK_ACCOUNT": ["iban", "account_num", "account_number", "routing_num"]
}

# False-positive exclusions: Column names that should NOT be classified as PII
FALSE_POSITIVE_EXCLUSIONS = {
    "product_id", "product_code", "item_id", "sku", "transaction_id", "order_id",
    "status_code", "category_id", "error_code", "zip_file", "event_id", "log_id"
}

class PIIDetector:
    def detect_pii_columns(self, df: pd.DataFrame, sample_size: int = 100) -> List[Dict[str, Any]]:
        """
        Inspects DataFrame schema and sample values to identify PII columns with confidence scoring.
        """
        detected: List[Dict[str, Any]] = []

        if df is None or df.empty:
            return detected

        sample_df = df.head(sample_size)

        for col in df.columns:
            col_str = str(col).strip()
            col_lower = col_str.lower()

            # Skip explicit non-PII false-positive exclusions
            if col_lower in FALSE_POSITIVE_EXCLUSIONS:
                continue

            category: Optional[str] = None
            confidence: float = 0.0
            reasons: List[str] = []

            # 1. Column Name Signal Matching
            for cat, keywords in COLUMN_NAME_SIGNALS.items():
                if any(kw == col_lower or f"_{kw}" in col_lower or f"{kw}_" in col_lower for kw in keywords):
                    category = cat
                    confidence += 0.55
                    reasons.append(f"Column name '{col_str}' matches PII keyword for {cat}")
                    break

            # 2. Value Pattern Matching on non-null string samples
            non_null_samples = sample_df[col].dropna().astype(str).str.strip().tolist()
            if non_null_samples and len(non_null_samples) > 0:
                # Test regex patterns
                for cat, pattern in PATTERNS.items():
                    matches = sum(1 for v in non_null_samples if pattern.match(v))
                    match_ratio = matches / len(non_null_samples)

                    if match_ratio >= 0.3:
                        if category == cat:
                            confidence = min(1.0, confidence + 0.45)
                        elif category is None:
                            category = cat
                            confidence = min(0.95, match_ratio * 0.9)

                        reasons.append(f"{round(match_ratio * 100)}% of sample values match pattern for {cat}")
                        break

            # 3. Person Name Heuristic (Strings with capital letters / spaces if col contains 'name')
            if category is None and "name" in col_lower:
                name_like_cnt = sum(1 for v in non_null_samples if len(v.split()) in [2, 3] and v[0].isupper())
                if non_null_samples and (name_like_cnt / len(non_null_samples)) >= 0.4:
                    category = "PERSON_NAME"
                    confidence = 0.85
                    reasons.append("Sample values resemble human names")

            # Filter out weak signals (< 0.5 confidence) to prevent false positives
            if category and confidence >= 0.5:
                rec_action = "MASK" if category in ["EMAIL", "PHONE", "CREDIT_CARD", "PERSON_NAME", "GOVERNMENT_ID"] else "ANONYMIZE"
                detected.append({
                    "column": col_str,
                    "category": category,
                    "confidence": round(confidence, 2),
                    "reasons": reasons,
                    "recommended_action": rec_action
                })

        return detected

pii_detector = PIIDetector()
