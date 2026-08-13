import math
import logging
from typing import List, Dict, Any, Optional
from services.chatbot.vector_store import vector_store
from core.config import settings

logger = logging.getLogger(__name__)


class BM25Retriever:
    """Lightweight in-memory BM25 lexical retrieval engine."""
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def search(self, chunks: List[Dict[str, Any]], query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not chunks or not query:
            return []

        q_terms = [t.lower() for t in query.split() if len(t) > 2]
        if not q_terms:
            return []

        N = len(chunks)
        doc_lengths = [len(c["text_content"].split()) for c in chunks]
        avgdl = sum(doc_lengths) / N if N > 0 else 1.0

        # Calculate Document Frequencies (DF)
        df = {}
        for term in q_terms:
            df[term] = sum(1 for c in chunks if term in c["text_content"].lower())

        scored_chunks = []
        for idx, c in enumerate(chunks):
            doc_text = c["text_content"].lower()
            doc_len = doc_lengths[idx]
            score = 0.0

            for term in q_terms:
                if df[term] == 0:
                    continue
                tf = doc_text.count(term)
                if tf == 0:
                    continue

                idf = math.log((N - df[term] + 0.5) / (df[term] + 0.5) + 1.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avgdl))
                score += idf * ((tf * (self.k1 + 1.0)) / denom)

            if score > 0:
                c_copy = dict(c)
                c_copy["bm25_score"] = float(round(score, 4))
                scored_chunks.append(c_copy)

        scored_chunks.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored_chunks[:top_k]


class HybridRetriever:
    def __init__(self):
        self.bm25_engine = BM25Retriever()

    def reciprocal_rank_fusion(self, vector_results: List[Dict[str, Any]], bm25_results: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
        """Combine dense vector search and BM25 lexical search using Reciprocal Rank Fusion (RRF)."""
        rrf_scores: Dict[str, float] = {}
        chunks_map: Dict[str, Dict[str, Any]] = {}

        for rank, res in enumerate(vector_results):
            cid = res["chunk_id"]
            chunks_map[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank + 1))

        for rank, res in enumerate(bm25_results):
            cid = res["chunk_id"]
            chunks_map[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank + 1))

        combined = []
        for cid, score in rrf_scores.items():
            item = dict(chunks_map[cid])
            item["rrf_score"] = float(round(score, 6))
            combined.append(item)

        combined.sort(key=lambda x: x["rrf_score"], reverse=True)
        return combined

    def retrieve(
        self,
        org_id: str,
        document_id: Optional[int],
        query: str,
        top_k: int = getattr(settings, "TOP_K_FINAL", 5)
    ) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Retrieval:
        1. Dense Vector Similarity Search
        2. BM25 Lexical Keyword Search
        3. Reciprocal Rank Fusion (RRF) Candidates
        4. Score Normalization & Reranking Top-K Output
        """
        top_k_vector = getattr(settings, "TOP_K_VECTOR", 10)
        top_k_bm25 = getattr(settings, "TOP_K_BM25", 10)

        # 1. Vector Search
        vector_candidates = vector_store.search_similar_chunks(org_id, document_id, query, top_k=top_k_vector)

        # 2. Get all tenant chunks for BM25 search
        tenant_keys = [k for k in vector_store.doc_chunks_index.keys() if k[0] == str(org_id)]
        if document_id is not None:
            tenant_keys = [k for k in tenant_keys if k[1] == int(document_id)]

        all_tenant_chunks = []
        for key in tenant_keys:
            v_chunks = vector_store.doc_chunks_index.get(key, [])
            for c in v_chunks:
                all_tenant_chunks.append({
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "org_id": c.org_id,
                    "page_number": c.page_number,
                    "section_title": c.section_title,
                    "text_content": c.text_content,
                    "similarity": 0.0,
                    "metadata": c.metadata
                })

        bm25_candidates = self.bm25_engine.search(all_tenant_chunks, query, top_k=top_k_bm25)

        # 3. Reciprocal Rank Fusion
        fused_candidates = self.reciprocal_rank_fusion(vector_candidates, bm25_candidates)

        # 4. Rerank & Score Normalization
        final_results = fused_candidates[:top_k]
        logger.info(f"HybridRetriever retrieved {len(final_results)} top context chunks for query='{query}'.")
        return final_results


hybrid_retriever = HybridRetriever()
