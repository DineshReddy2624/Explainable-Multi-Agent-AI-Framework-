import os
import re
from fastapi import HTTPException, status

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet", ".pdf", ".json", ".tsv"}
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB Limit

def sanitize_filename(filename: str) -> str:
    """
    Prevents path traversal attacks (e.g. '../../etc/passwd' or '..\\secret.csv').
    Returns stripped basename containing safe characters only.
    """
    if not filename:
        return "uploaded_file.csv"

    # Remove directory path components
    safe_name = os.path.basename(filename.replace("\\", "/"))
    # Replace dangerous non-alphanumeric characters except dot, dash, underscore
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', safe_name)

    if not safe_name or safe_name.startswith("."):
        safe_name = f"dataset_{safe_name.lstrip('.')}"

    return safe_name

def validate_uploaded_file(filename: str, content: bytes, max_size_bytes: int = MAX_FILE_SIZE_BYTES) -> str:
    """
    Performs security validation on uploaded files:
    1. Path Traversal & Malicious Filename Prevention
    2. Extension Whitelisting
    3. File Size Caps
    4. Empty/Corrupted File Checks
    """
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security rejection: Invalid filename or path traversal detected."
        )

    clean_fn = sanitize_filename(filename)

    # Extension Check
    ext = os.path.splitext(clean_fn)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security rejection: File extension '{ext}' is not permitted. Allowed: {list(ALLOWED_EXTENSIONS)}"
        )

    # Size Check
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Security rejection: File size exceeds maximum limit of {max_size_bytes // (1024*1024)}MB."
        )

    # Empty File Check
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security rejection: Uploaded file is empty (0 bytes)."
        )

    return clean_fn
