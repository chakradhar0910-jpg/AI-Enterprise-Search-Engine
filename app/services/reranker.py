import threading
from typing import List, Dict, Any, Tuple


class RerankerService:
    """Cross-encoder reranker for fine-grained query-passage relevance assessment."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(RerankerService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        if getattr(self, "_initialized", False):
            return

        self.model_name = model_name
        self._model = None
        self._load_failed = False
        self._model_lock = threading.Lock()
        self._initialized = True

    def get_model(self):
        """Lazy loader for CrossEncoder."""
        if self._model is None and not self._load_failed:
            with self._model_lock:
                if self._model is None and not self._load_failed:
                    try:
                        from sentence_transformers import CrossEncoder
                        print(f"[RerankerService] Loading CrossEncoder: {self.model_name}...")
                        self._model = CrossEncoder(self.model_name)
                        print("[RerankerService] CrossEncoder loaded successfully.")
                    except Exception as e:
                        print(f"[RerankerService] CrossEncoder load notice ({e}). Falling back to hybrid score.")
                        self._load_failed = True
        return self._model

    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank candidate passages.
        Uses CrossEncoder neural scoring when available, with a weighted query-overlap fallback.
        """
        if not candidate_chunks:
            return []

        model = self.get_model()

        if model is not None:
            try:
                pairs = [[query, c.get("chunk_text", "")] for c in candidate_chunks]
                scores = model.predict(pairs)
                for i, score in enumerate(scores):
                    candidate_chunks[i]["rerank_score"] = float(score)
                candidate_chunks.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
                return candidate_chunks[:top_k]
            except Exception as e:
                print(f"[RerankerService] CrossEncoder prediction notice: {e}")

        # Intelligent Fallback: Blend term match density with retrieval rank score
        query_words = set(query.lower().split())
        for c in candidate_chunks:
            text_words = set(c.get("chunk_text", "").lower().split())
            overlap = len(query_words.intersection(text_words))
            base_score = float(c.get("fused_score", c.get("similarity", 0.0)))
            c["rerank_score"] = base_score + (overlap * 0.5)

        candidate_chunks.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return candidate_chunks[:top_k]
