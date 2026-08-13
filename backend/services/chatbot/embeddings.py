import logging
import numpy as np
from typing import List, Union
from core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        """Initialize local Transformer embedding model (SentenceTransformer)."""
        if self._model is not None:
            return

        model_name = getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        provider = getattr(settings, "EMBEDDING_PROVIDER", "sentence-transformers")

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
            self._use_transformer = True
            logger.info(f"Successfully loaded SentenceTransformer model '{model_name}'.")
        except Exception as e:
            self._model = None
            self._use_transformer = False
            logger.warning(f"SentenceTransformer model '{model_name}' could not be loaded: {str(e)}")

            if settings.ENVIRONMENT.lower() == "production" and provider == "sentence-transformers":
                raise RuntimeError(
                    f"FATAL EMBEDDING ERROR: Production environment requires valid '{model_name}' Transformer model, "
                    f"but initialization failed: {str(e)}"
                )

    def embed_text(self, text: str) -> List[float]:
        """Generate a dense 384-dimensional normalized embedding vector for a single string."""
        dim = getattr(settings, "EMBEDDING_DIMENSION", 384)
        if not text or not str(text).strip():
            return [0.0] * dim

        clean_text = str(text).strip()

        if self._use_transformer and self._model is not None:
            try:
                embedding = self._model.encode(clean_text, convert_to_numpy=True, normalize_embeddings=True)
                return embedding.astype(float).tolist()
            except Exception as e:
                logger.error(f"Transformer embedding generation failed: {str(e)}")
                if settings.ENVIRONMENT.lower() == "production":
                    raise

        # Fallback local deterministic dense projection (development/test only)
        return self._local_dense_embedding(clean_text, dim=dim)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized embeddings for a list of strings in batch."""
        dim = getattr(settings, "EMBEDDING_DIMENSION", 384)
        if not texts:
            return []

        clean_texts = [str(t).strip() if (t and str(t).strip()) else " " for t in texts]

        if self._use_transformer and self._model is not None:
            try:
                batch_size = getattr(settings, "EMBEDDING_BATCH_SIZE", 32)
                embeddings = self._model.encode(clean_texts, batch_size=batch_size, convert_to_numpy=True, normalize_embeddings=True)
                return [emb.astype(float).tolist() for emb in embeddings]
            except Exception as e:
                logger.error(f"Batch transformer embedding generation failed: {str(e)}")
                if settings.ENVIRONMENT.lower() == "production":
                    raise

        return [self.embed_text(t) for t in clean_texts]

    def get_embedding(self, text: str) -> List[float]:
        """Backward-compatibility wrapper."""
        return self.embed_text(text)

    def cosine_similarity(self, vec1: Union[List[float], np.ndarray], vec2: Union[List[float], np.ndarray]) -> float:
        """Compute cosine similarity between two vector embeddings."""
        v1 = np.array(vec1, dtype=float)
        v2 = np.array(vec2, dtype=float)

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        sim = float(np.dot(v1, v2) / (norm1 * norm2))
        return float(max(-1.0, min(1.0, sim)))

    def _local_dense_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Local fallback dense embedding generator for development/test mode."""
        words = text.lower().split()
        vec = np.zeros(dim, dtype=float)
        for idx, word in enumerate(words):
            for char_idx, char in enumerate(word):
                pos = (ord(char) * 17 + idx * 31 + char_idx * 7) % dim
                vec[pos] += 1.0 / (char_idx + 1)

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


embedding_service = EmbeddingService()
