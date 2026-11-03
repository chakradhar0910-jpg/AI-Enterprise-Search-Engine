import json
import os
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


class VectorStore:
    """Persistent vector store manager using FAISS and json metadata mapping."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(VectorStore, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, index_dir: Optional[str] = None, dimension: int = 384):
        if getattr(self, "_initialized", False):
            return

        self.index_dir = Path(index_dir) if index_dir else Path("data/vector_store")
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "index.faiss"
        self.metadata_path = self.index_dir / "metadata.json"

        self.dimension = dimension
        self.index = None
        # Mapping from faiss_id (str) to metadata dictionary:
        # { "chunk_id": int, "document_id": int, "department_id": int or None }
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._next_id = 0
        self._lock = threading.Lock()

        self._load_or_initialize()
        self._initialized = True

    def _load_or_initialize(self) -> None:
        """Load FAISS index and metadata from disk, or initialize fresh index."""
        import faiss

        with self._lock:
            if self.index_path.exists() and self.metadata_path.exists():
                try:
                    self.index = faiss.read_index(str(self.index_path))
                    with open(self.metadata_path, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                    # Determine next ID
                    if self.metadata:
                        self._next_id = max(int(k) for k in self.metadata.keys()) + 1
                    else:
                        self._next_id = 0
                    print(f"[VectorStore] Successfully loaded FAISS index with {self.index.ntotal} vectors.")
                    return
                except Exception as e:
                    print(f"[VectorStore] Warning: Could not read existing index ({e}), creating a new one.")

            # Create new index using Inner Product (Cosine Similarity when normalized)
            base_index = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIDMap(base_index)
            self.metadata = {}
            self._next_id = 0
            self._save_unlocked()

    def _save_unlocked(self) -> None:
        """Persist index and metadata to disk (assumes lock is held)."""
        import faiss
        try:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"[VectorStore] Error persisting index to disk: {e}")

    def add_vectors(self, embeddings: np.ndarray, chunks_metadata: List[Dict[str, Any]]) -> List[int]:
        """
        Add batch of vector embeddings and associated metadata to index.
        Returns the assigned FAISS IDs.
        """
        if len(embeddings) == 0:
            return []

        import faiss
        with self._lock:
            num_vectors = embeddings.shape[0]
            ids = np.arange(self._next_id, self._next_id + num_vectors, dtype=np.int64)

            # Ensure embeddings are float32
            emb_float32 = np.ascontiguousarray(embeddings, dtype=np.float32)

            # Add to FAISS IndexIDMap
            self.index.add_with_ids(emb_float32, ids)

            # Store metadata for each vector
            assigned_ids = []
            for i, meta in enumerate(chunks_metadata):
                faiss_id = int(ids[i])
                self.metadata[str(faiss_id)] = {
                    "chunk_id": meta.get("chunk_id"),
                    "document_id": meta.get("document_id"),
                    "department_id": meta.get("department_id"),
                    "page_number": meta.get("page_number"),
                    "section_title": meta.get("section_title")
                }
                assigned_ids.append(faiss_id)

            self._next_id += num_vectors
            self._save_unlocked()
            return assigned_ids

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        allowed_document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using cosine similarity.
        Applies permission / document filtering on retrieved results.
        Returns list of matching chunks with 'faiss_id', 'chunk_id', 'document_id', and 'similarity'.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        with self._lock:
            # Query FAISS for a larger candidate pool to allow post-filtering
            candidate_k = min(self.index.ntotal, max(top_k * 5, 20))
            q_emb = np.ascontiguousarray(query_embedding.reshape(1, -1), dtype=np.float32)

            distances, indices = self.index.search(q_emb, candidate_k)

            results = []
            allowed_set = set(allowed_document_ids) if allowed_document_ids is not None else None

            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:
                    continue

                faiss_id_str = str(idx)
                meta = self.metadata.get(faiss_id_str)
                if not meta:
                    continue

                doc_id = meta.get("document_id")
                # Filter by allowed document IDs for authorization
                if allowed_set is not None and doc_id not in allowed_set:
                    continue

                results.append({
                    "faiss_id": int(idx),
                    "chunk_id": meta.get("chunk_id"),
                    "document_id": doc_id,
                    "department_id": meta.get("department_id"),
                    "page_number": meta.get("page_number"),
                    "section_title": meta.get("section_title"),
                    "similarity": float(dist)  # Inner product of normalized vectors = Cosine Similarity
                })

                if len(results) >= top_k:
                    break

            return results

    def remove_document_vectors(self, document_id: int) -> int:
        """
        Remove all vectors associated with a document_id.
        Rebuilds index to ensure no ghost entries persist.
        """
        import faiss

        with self._lock:
            ids_to_remove = [
                int(fid) for fid, meta in self.metadata.items()
                if meta.get("document_id") == document_id
            ]

            if not ids_to_remove:
                return 0

            # Remove IDs from index
            remove_arr = np.array(ids_to_remove, dtype=np.int64)
            self.index.remove_ids(remove_arr)

            # Clean metadata
            for fid in ids_to_remove:
                self.metadata.pop(str(fid), None)

            self._save_unlocked()
            print(f"[VectorStore] Removed {len(ids_to_remove)} vectors for document {document_id}")
            return len(ids_to_remove)

    def total_vectors(self) -> int:
        """Return total number of vectors in index."""
        if self.index:
            return self.index.ntotal
        return 0
