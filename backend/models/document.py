import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String(100), index=True, nullable=False, default="org_default")
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Float, nullable=False, default=0.0)
    file_type = Column(String(50), nullable=False)
    file_hash = Column(String(64), index=True, nullable=True)
    status = Column(String(50), default="UPLOADED", nullable=False)  # UPLOADED, PARSED, INDEXED, ERROR
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    org_id = Column(String(100), index=True, nullable=False)
    version_number = Column(Integer, default=1, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Float, default=0.0)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="versions")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=True)
    org_id = Column(String(100), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False, default=0)
    page_number = Column(Integer, nullable=True, default=1)
    section_title = Column(String(255), nullable=True)
    text_content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="chunks")
