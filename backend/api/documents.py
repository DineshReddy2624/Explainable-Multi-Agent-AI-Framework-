import os
import hashlib
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.tenant_security import get_tenant_context
from core.response import StandardResponse
from core.config import settings
from core.file_security import validate_uploaded_file, sanitize_filename
from models.document import Document, DocumentVersion, DocumentChunk
from services.documents.document_parsers import document_parser_factory
from services.documents.chunking_engine import chunking_engine
from services.chatbot.vector_store import vector_store

router = APIRouter()
active_documents_cache: Dict[int, Dict[str, Any]] = {}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant: dict = Depends(get_tenant_context)
):
    filename = file.filename
    content = await file.read()
    org_id = tenant.get("org_id", "org_default")
    user_id = tenant.get("user_id", 1)

    # 1. File Security & Validation
    try:
        clean_filename = validate_uploaded_file(filename, content)
    except Exception as e:
        clean_filename = sanitize_filename(filename)

    file_hash = hashlib.sha256(content).hexdigest()
    file_type = clean_filename.rsplit('.', 1)[-1].lower()

    # 2. Save Document to tenant directory
    tenant_doc_dir = os.path.join(settings.DOCUMENTS_DIR, "organizations", org_id)
    os.makedirs(tenant_doc_dir, exist_ok=True)
    doc_path = os.path.join(tenant_doc_dir, f"doc_{file_hash[:12]}_{clean_filename}")

    with open(doc_path, "wb") as f:
        f.write(content)

    # 3. Create Document DB record
    db_doc = Document(
        org_id=org_id,
        owner_user_id=user_id,
        filename=clean_filename,
        file_path=doc_path,
        file_size=float(len(content)),
        file_type=file_type,
        file_hash=file_hash,
        status="PARSING"
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    document_id = db_doc.id

    # 4. Parse document & Chunk text
    parser = document_parser_factory.get_parser(clean_filename)
    parsed_doc = parser.parse(doc_path, clean_filename)
    chunks = chunking_engine.chunk_document(parsed_doc, document_id=document_id, org_id=org_id)

    # 5. Save DocumentChunks to DB & VectorStore
    db_doc.page_count = parsed_doc.total_pages
    db_doc.chunk_count = len(chunks)
    db_doc.status = "INDEXED"

    for chunk in chunks:
        db_chunk = DocumentChunk(
            document_id=document_id,
            org_id=org_id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            text_content=chunk.text,
            metadata_json=chunk.metadata
        )
        db.add(db_chunk)

    db.commit()

    # Index in VectorStore
    vector_store.add_document_chunks(org_id=org_id, document_id=document_id, chunks=chunks)

    active_documents_cache[document_id] = {
        "document_id": document_id,
        "filename": clean_filename,
        "page_count": parsed_doc.total_pages,
        "chunk_count": len(chunks),
        "parsed_doc": parsed_doc,
        "chunks": [c.to_dict() for c in chunks]
    }

    payload = {
        "document_id": document_id,
        "id": document_id,
        "filename": clean_filename,
        "file_type": file_type,
        "page_count": parsed_doc.total_pages,
        "chunk_count": len(chunks),
        "status": "INDEXED"
    }

    return StandardResponse.ok(data=payload, message=f"Successfully uploaded and indexed document '{clean_filename}'.")


@router.get("")
def list_documents(db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    org_id = tenant.get("org_id", "org_default")
    docs = db.query(Document).filter(Document.org_id == org_id).order_by(Document.id.desc()).all()
    results = [
        {
            "id": d.id,
            "document_id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "page_count": d.page_count,
            "chunk_count": d.chunk_count,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in docs
    ]
    return StandardResponse.ok(data=results)


@router.get("/{document_id}/status")
def get_document_status(document_id: int, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    org_id = tenant.get("org_id", "org_default")
    doc = db.query(Document).filter(Document.id == document_id, Document.org_id == org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document #{document_id} not found.")

    return StandardResponse.ok(data={
        "document_id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "page_count": doc.page_count,
        "chunk_count": doc.chunk_count
    })


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    org_id = tenant.get("org_id", "org_default")
    doc = db.query(Document).filter(Document.id == document_id, Document.org_id == org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document #{document_id} not found.")

    db.delete(doc)
    db.commit()
    active_documents_cache.pop(document_id, None)

    return StandardResponse.ok(message=f"Document #{document_id} deleted successfully.")
