import os
import threading
from typing import List, Union
import numpy as np


class EmbeddingService:
    """Thread-safe singleton service for generating dense semantic vector embeddings."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(EmbeddingService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        if getattr(self, "_initialized", False):
            return

        self.model_name = model_name
        self._model = None
        self._model_lock = threading.Lock()
        self._dimension = 384  # default for all-MiniLM-L6-v2
        self._initialized = True

    def get_model(self):
        """Lazy loader for SentenceTransformer model."""
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                        print(f"[EmbeddingService] Loading model: {self.model_name}...")
                        self._model = SentenceTransformer(self.model_name)
                        # Check vector dimension
                        test_emb = self._model.encode(["test"], normalize_embeddings=True)
                        self._dimension = test_emb.shape[1]
                        print(f"[EmbeddingService] Model loaded successfully. Dimension: {self._dimension}")
                    except Exception as e:
                        print(f"[EmbeddingService] Error loading SentenceTransformer: {e}")
                        raise RuntimeError(f"Could not initialize embedding model '{self.model_name}': {e}")
        return self._model

    @property
    def dimension(self) -> int:
        """Returns the vector embedding dimension."""
        return self._dimension

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Encode text or list of texts into normalized numpy array of float32.
        Normalized vectors enable inner-product dot product to match Cosine Similarity.
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.empty((0, self._dimension), dtype=np.float32)

        model = self.get_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings.astype(np.float32)

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a single natural language search query."""
        emb = self.encode([query])
        return emb[0]
