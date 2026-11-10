from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    avatar_url = Column(String, default="", nullable=True)
    role = Column(String, default="ANALYST")

    google_id = Column(String, unique=True, index=True, nullable=True)
    auth_provider = Column(String, default="local", nullable=True)

    org_id = Column(String, nullable=False, index=True, default="org_default")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

