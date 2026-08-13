import re
import pandas as pd
from typing import List, Dict, Any, Tuple

def mask_email(val: Any) -> str:
    val_str = str(val).strip()
    if not val_str or "@" not in val_str:
        return "***MASKED***"
    parts = val_str.split("@", 1)
    username = parts[0]
    domain = parts[1]
    if len(username) <= 1:
        masked_user = "*"
    else:
        masked_user = username[0] + "*" * (len(username) - 1)
    return f"{masked_user}@{domain}"

def mask_phone(val: Any) -> str:
    val_str = str(val).strip()
    digits = re.sub(r'\D', '', val_str)
    if len(digits) >= 4:
        return "*" * (len(digits) - 4) + digits[-4:]
    return "******"

def mask_credit_card(val: Any) -> str:
    val_str = str(val).strip()
    digits = re.sub(r'\D', '', val_str)
    if len(digits) >= 4:
        return "*" * (len(digits) - 4) + digits[-4:]
    return "************"

def mask_person_name(val: Any) -> str:
    val_str = str(val).strip()
    words = val_str.split()
    masked_words = []
    for w in words:
        if len(w) <= 1:
            masked_words.append("*")
        else:
            masked_words.append(w[0] + "*" * (len(w) - 1))
    return " ".join(masked_words) if masked_words else "***MASKED***"

def mask_generic(val: Any) -> str:
    return "***MASKED***"

MASK_FUNCTIONS = {
    "EMAIL": mask_email,
    "PHONE": mask_phone,
    "CREDIT_CARD": mask_credit_card,
    "PERSON_NAME": mask_person_name,
    "GOVERNMENT_ID": mask_generic,
    "PASSPORT": mask_generic,
    "BANK_ACCOUNT": mask_generic,
    "ADDRESS": mask_generic,
    "POSTAL_CODE": mask_generic
}

class PIIMasker:
    def mask_dataframe(self, df: pd.DataFrame, pii_classifications: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, List[str]]:
        """
        Creates a new masked DataFrame preserving original values in raw dataset storage.
        """
        if df is None or df.empty:
            return df.copy() if df is not None else pd.DataFrame(), []

        masked_df = df.copy()
        logs: List[str] = []

        for pii in pii_classifications:
            col = pii.get("column")
            cat = pii.get("category", "GENERIC").upper()

            if col in masked_df.columns:
                mask_fn = MASK_FUNCTIONS.get(cat, mask_generic)
                masked_df[col] = masked_df[col].apply(lambda x: mask_fn(x) if pd.notnull(x) else x)
                logs.append(f"Applied PII masking ({cat}) to column '{col}'")

        return masked_df, logs

pii_masker = PIIMasker()
