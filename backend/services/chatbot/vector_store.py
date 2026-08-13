import logging
from typing import List, Dict, Any, Optional, Tuple
from services.chatbot.embeddings import embedding_service
from services.documents.chunking_engine import TextChunk

logger = logging.getLogger(__name__)


class ColumnVectorDocument:
    def __init__(self, column_name: str, data_type: str, synonyms: Optional[List[str]] = None, description: Optional[str] = None):
        self.column_name = column_name
        self.normalized_name = column_name.lower().replace('_', ' ')
        self.data_type = data_type
        self.synonyms = synonyms or []
        self.description = description or f"{self.normalized_name} column"

        # Build rich semantic representation
        syn_str = ", ".join(self.synonyms) if self.synonyms else self.normalized_name
        self.text_content = (
            f"Column: {self.column_name}\n"
            f"Normalized name: {self.normalized_name}\n"
            f"Data type: {self.data_type}\n"
            f"Description: {self.description}\n"
            f"Synonyms: {syn_str}"
        )
        self.embedding: List[float] = []


class VectorChunkDocument:
    def __init__(self, chunk_id: str, document_id: int, org_id: str, page_number: int, section_title: Optional[str], text_content: str, metadata: Dict[str, Any]):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.org_id = org_id
        self.page_number = page_number
        self.section_title = section_title
        self.text_content = text_content
        self.metadata = metadata
        self.embedding: List[float] = []


class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            # Store schema columns: store_index[(org_id, dataset_id)] = List[ColumnVectorDocument]
            cls._instance.store_index: Dict[Tuple[str, Any], List[ColumnVectorDocument]] = {}
            # Store document chunks: doc_chunks_index[(org_id, document_id)] = List[VectorChunkDocument]
            cls._instance.doc_chunks_index: Dict[Tuple[str, Any], List[VectorChunkDocument]] = {}
        return cls._instance

    def add_column_documents(self, org_id: str, dataset_id: Any, columns_meta: List[Dict[str, Any]]) -> bool:
        """
        Build and index semantic column documents for a dataset, strictly scoped by org_id and dataset_id.
        Enforces tenant isolation and PII safety (schema-only indexing, no raw PII rows).
        """
        if not org_id or dataset_id is None:
            return False

        key = (str(org_id), str(dataset_id))
        docs: List[ColumnVectorDocument] = []

        synonym_map = {
            "customer": ["customer", "client", "user", "buyer"],
            "client": ["client", "customer", "company"],
            "employee": ["employee", "staff", "worker"],
            "patient": ["patient", "subject", "individual"],
            "amount": ["spending", "spend", "purchase value", "transaction amount", "customer spend", "cost", "price", "loan amount", "payment"],
            "cost": ["treatment cost", "purchase amount", "price", "cost", "expense"],
            "salary": ["monthly salary", "annual income", "salary", "compensation", "pay", "monthly income", "earnings", "wage"],
            "income": ["annual income", "monthly income", "monthly salary", "revenue", "salary", "household income", "earnings", "pay"],
            "spending": ["purchase amount", "total spent", "spending", "spend", "expenditure"],
            "age": ["age", "years old", "years of age"],
            "score": ["credit score", "fraud score", "risk score", "performance rating", "rating"],
            "status": ["account status", "approval status", "status", "employment status"],
            "department": ["department", "dept", "unit", "division", "team"]
        }

        for meta in columns_meta:
            col_name = meta.get("name") or meta.get("column")
            if not col_name:
                continue

            dtype = str(meta.get("data_type") or meta.get("dtype") or "string")
            col_lower = str(col_name).lower()
            is_id_col = col_lower.endswith("_id") or col_lower.endswith("id") or col_lower == "id"
            col_synonyms = set([col_lower, col_lower.replace('_', ' ')])
            for k, syns in synonym_map.items():
                if is_id_col and k in ["employee", "customer", "patient", "client", "user"]:
                    continue
                if k in col_lower or any(s in col_lower for s in syns):
                    col_synonyms.update(syns)

            doc = ColumnVectorDocument(
                column_name=str(col_name),
                data_type=dtype,
                synonyms=list(col_synonyms),
                description=meta.get("description", f"{col_name.replace('_', ' ')} column")
            )
            doc.embedding = embedding_service.embed_text(doc.text_content)
            docs.append(doc)

        self.store_index[key] = docs
        return True

    def search_similar_columns(
        self,
        org_id: str,
        dataset_id: Any,
        query_text: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        key = (str(org_id), str(dataset_id))
        docs = self.store_index.get(key, [])
        if not docs or not query_text:
            return []

        query_emb = embedding_service.embed_text(query_text)
        results = []

        for doc in docs:
            sim = embedding_service.cosine_similarity(query_emb, doc.embedding)

            q_low = query_text.lower()
            col_low = doc.column_name.lower()
            is_id_col = col_low.endswith("_id") or col_low.endswith("id") or col_low == "id"
            is_metric_query = any(m in q_low for m in ["pay", "salary", "amount", "spend", "cost", "income", "earnings", "price", "revenue", "total", "average", "sum", "rate", "ratio", "score"])

            if any(s in q_low for s in doc.synonyms if len(s) > 2):
                if not (is_id_col and is_metric_query):
                    sim = min(1.0, sim + 0.15)
            if doc.normalized_name in q_low or q_low in doc.normalized_name:
                sim = min(1.0, sim + 0.25)

            if is_metric_query and not is_id_col and any(t in doc.data_type.lower() for t in ["float", "int", "number"]):
                sim = min(1.0, sim + 0.10)

            results.append({
                "column": doc.column_name,
                "similarity": float(round(sim, 4)),
                "data_type": doc.data_type,
                "text_content": doc.text_content,
                "method": "embedding"
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def add_document_chunks(self, org_id: str, document_id: int, chunks: List[TextChunk]) -> bool:
        """
        Index document text chunks with dense embeddings for RAG retrieval.
        Enforces tenant isolation by org_id and document_id.
        """
        if not org_id or document_id is None or not chunks:
            return False

        key = (str(org_id), int(document_id))
        texts = [c.text for c in chunks]
        embeddings = embedding_service.embed_batch(texts)

        vector_chunks: List[VectorChunkDocument] = []
        for idx, chunk in enumerate(chunks):
            v_doc = VectorChunkDocument(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                org_id=chunk.org_id,
                page_number=chunk.page_number,
                section_title=chunk.section_title,
                text_content=chunk.text,
                metadata=chunk.metadata
            )
            v_doc.embedding = embeddings[idx]
            vector_chunks.append(v_doc)

        self.doc_chunks_index[key] = vector_chunks
        logger.info(f"Indexed {len(vector_chunks)} document chunks for doc_id={document_id}, org_id={org_id}.")
        return True

    def search_similar_chunks(
        self,
        org_id: str,
        document_id: Optional[int],
        query_text: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search document text chunks by vector similarity.
        Enforces strict tenant isolation by org_id.
        """
        if not org_id or not query_text:
            return []

        query_emb = embedding_service.embed_text(query_text)
        results = []

        # Find matching document keys for tenant
        matching_keys = [k for k in self.doc_chunks_index.keys() if k[0] == str(org_id)]
        if document_id is not None:
            matching_keys = [k for k in matching_keys if k[1] == int(document_id)]

        for key in matching_keys:
            chunks = self.doc_chunks_index.get(key, [])
            for c in chunks:
                sim = embedding_service.cosine_similarity(query_emb, c.embedding)
                results.append({
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "org_id": c.org_id,
                    "page_number": c.page_number,
                    "section_title": c.section_title,
                    "text_content": c.text_content,
                    "similarity": float(round(sim, 4)),
                    "metadata": c.metadata
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def clear_index(self, org_id: Optional[str] = None, dataset_id: Optional[Any] = None):
        """Clear indexed vector store documents."""
        if org_id and dataset_id is not None:
            self.store_index.pop((str(org_id), str(dataset_id)), None)
        elif org_id:
            keys_to_remove = [k for k in self.store_index.keys() if k[0] == str(org_id)]
            for k in keys_to_remove:
                self.store_index.pop(k, None)
            doc_keys_to_remove = [k for k in self.doc_chunks_index.keys() if k[0] == str(org_id)]
            for k in doc_keys_to_remove:
                self.doc_chunks_index.pop(k, None)
        else:
            self.store_index.clear()
            self.doc_chunks_index.clear()


vector_store = VectorStore()
