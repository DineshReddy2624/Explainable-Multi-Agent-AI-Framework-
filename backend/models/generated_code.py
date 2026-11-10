from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime
from core.database import Base


class GeneratedCode(Base):
    """Database model for storing AI-generated Python remediation scripts, SQL queries, and code artifacts."""
    __tablename__ = "generated_codes"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    org_id = Column(String, nullable=False, default="org_default")
    code_type = Column(String, nullable=False)  # PYTHON_REMEDIATION_SCRIPT, SQL_TRANSFORMATION_QUERY, PROFILING_SCRIPT, BEFORE_AFTER_PDF
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    code_content = Column(Text, nullable=False)
    digital_hash = Column(String, nullable=False)
    execution_status = Column(String, nullable=False, default="EXECUTED")
    created_at = Column(DateTime, default=datetime.utcnow)

