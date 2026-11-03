import re
import threading
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi


class KeywordSearchService:
    """BM25-based keyword search service for exact term, entity, and code retrieval."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(KeywordSearchService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._lock = threading.Lock()
        # List of items: {"chunk_id": int, "document_id": int, "tokens": list[str]}
        self.corpus_entries: List[Dict[str, Any]] = []
        self.bm25_model: Optional[BM25Okapi] = None
        self._initialized = True

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple tokenization: lowercase alphanumeric tokens."""
        if not text:
            return []
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
        return tokens

    def rebuild_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Rebuild BM25 index from a list of chunk dictionaries:
        [{'chunk_id': int, 'document_id': int, 'chunk_text': str}, ...]
        """
        with self._lock:
            self.corpus_entries = []
            tokenized_corpus = []

            for chk in chunks:
                tokens = self.tokenize(chk.get("chunk_text", ""))
                if tokens:
                    self.corpus_entries.append({
                        "chunk_id": chk.get("chunk_id"),
                        "document_id": chk.get("document_id"),
                        "tokens": tokens
                    })
                    tokenized_corpus.append(tokens)

            if tokenized_corpus:
                self.bm25_model = BM25Okapi(tokenized_corpus)
                print(f"[KeywordSearch] Built BM25 index with {len(tokenized_corpus)} passages.")
            else:
                self.bm25_model = None

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Add new chunks to the BM25 index and re-index."""
        with self._lock:
            new_entries = []
            for chk in chunks:
                tokens = self.tokenize(chk.get("chunk_text", ""))
                if tokens:
                    new_entries.append({
                        "chunk_id": chk.get("chunk_id"),
                        "document_id": chk.get("document_id"),
                        "tokens": tokens
                    })

            self.corpus_entries.extend(new_entries)
            all_tokens = [e["tokens"] for e in self.corpus_entries]
            if all_tokens:
                self.bm25_model = BM25Okapi(all_tokens)

    def remove_document(self, document_id: int) -> None:
        """Remove chunks belonging to a document and rebuild."""
        with self._lock:
            self.corpus_entries = [e for e in self.corpus_entries if e["document_id"] != document_id]
            all_tokens = [e["tokens"] for e in self.corpus_entries]
            if all_tokens:
                self.bm25_model = BM25Okapi(all_tokens)
            else:
                self.bm25_model = None

    def search(
        self,
        query: str,
        top_k: int = 5,
        allowed_document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute BM25 keyword search.
        Returns list of dicts with 'chunk_id', 'document_id', and 'score'.
        """
        if not self.bm25_model or not self.corpus_entries:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        with self._lock:
            scores = self.bm25_model.get_scores(query_tokens)
            candidates = []
            allowed_set = set(allowed_document_ids) if allowed_document_ids is not None else None
            query_set = set(query_tokens)

            for i, score in enumerate(scores):
                entry = self.corpus_entries[i]
                query_overlap = query_set.intersection(entry.get("tokens", []))
                if not query_overlap and score <= 0.0:
                    continue

                doc_id = entry["document_id"]
                if allowed_set is not None and doc_id not in allowed_set:
                    continue

                effective_score = float(score) if score > 0.0 else float(len(query_overlap))

                candidates.append({
                    "chunk_id": entry["chunk_id"],
                    "document_id": doc_id,
                    "score": effective_score
                })

            # Sort descending by score
            candidates.sort(key=lambda x: x["score"], reverse=True)
            return candidates[:top_k]
