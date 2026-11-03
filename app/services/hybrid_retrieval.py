from typing import List, Dict, Any, Optional
from app.models import Document, DocumentChunk, DocumentPermission, User
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.keyword_search import KeywordSearchService
from app.services.reranker import RerankerService


class HybridRetriever:
    """Combines dense semantic search (FAISS) and sparse lexical search (BM25) with Reciprocal Rank Fusion and Reranking."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.keyword_service = KeywordSearchService()
        self.reranker = RerankerService()

    @staticmethod
    def get_authorized_document_ids(user: User) -> List[int]:
        """
        Determine list of document IDs the current user is authorized to read.
        Enforces department-level boundaries and ownership.
        """
        if not user or not user.is_authenticated:
            return []

        # Administrators have access to all documents
        if user.is_admin:
            docs = Document.query.with_entities(Document.id).filter_by(indexing_status="Indexed").all()
            return [d.id for d in docs]

        # Regular users can access:
        # 1. Documents they uploaded themselves
        # 2. Documents in their department or with general/None department
        # 3. Documents explicitly permitted to their department or marked public
        user_dept_id = user.department_id

        # Query permitted document IDs
        permitted_ids = set()

        # Public or user's department permissions
        perm_query = DocumentPermission.query.filter(
            (DocumentPermission.is_public == True) |  # noqa: E712
            (DocumentPermission.department_id == user_dept_id)
        ).with_entities(DocumentPermission.document_id).all()
        for p in perm_query:
            permitted_ids.add(p.document_id)

        # Base query for documents
        base_query = Document.query.filter(
            Document.indexing_status == "Indexed"
        ).filter(
            (Document.uploaded_by == user.id) |
            (Document.department_id == user_dept_id) |
            (Document.department_id.is_(None)) |
            (Document.id.in_(permitted_ids))
        ).with_entities(Document.id).all()

        return [d.id for d in base_query]

    def retrieve(
        self,
        query: str,
        user: User,
        top_k: int = 5,
        search_mode: str = "hybrid"  # "hybrid", "semantic", "keyword"
    ) -> List[Dict[str, Any]]:
        """
        Execute retrieval pipeline:
        1. Access verification
        2. Candidate retrieval (Semantic and/or BM25)
        3. Reciprocal Rank Fusion (RRF)
        4. Cross-Encoder reranking
        """
        allowed_doc_ids = self.get_authorized_document_ids(user)
        if not allowed_doc_ids:
            return []

        candidate_pool_size = max(top_k * 4, 15)

        semantic_results = []
        keyword_results = []

        # 1. Dense Semantic Search
        if search_mode in ("hybrid", "semantic"):
            try:
                query_emb = self.embedding_service.encode_query(query)
                semantic_results = self.vector_store.search(
                    query_embedding=query_emb,
                    top_k=candidate_pool_size,
                    allowed_document_ids=allowed_doc_ids
                )
            except Exception as e:
                print(f"[HybridRetriever] Semantic search notice: {e}")

        # 2. Sparse BM25 Keyword Search
        if search_mode in ("hybrid", "keyword"):
            try:
                keyword_results = self.keyword_service.search(
                    query=query,
                    top_k=candidate_pool_size,
                    allowed_document_ids=allowed_doc_ids
                )
            except Exception as e:
                print(f"[HybridRetriever] BM25 keyword search notice: {e}")

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF score: 1 / (k + rank) with k=60 standard
        K_RRF = 60
        fused_scores: Dict[int, float] = {}
        semantic_ranks: Dict[int, int] = {}
        keyword_ranks: Dict[int, int] = {}

        for rank, res in enumerate(semantic_results):
            cid = res["chunk_id"]
            semantic_ranks[cid] = rank + 1
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (K_RRF + rank + 1))

        for rank, res in enumerate(keyword_results):
            cid = res["chunk_id"]
            keyword_ranks[cid] = rank + 1
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (K_RRF + rank + 1))

        if not fused_scores:
            return []

        # Sort candidate chunk IDs by fused score
        sorted_chunk_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)
        top_chunk_ids = sorted_chunk_ids[:candidate_pool_size]

        # Fetch Chunk and Document records from database
        chunks_db = DocumentChunk.query.filter(DocumentChunk.id.in_(top_chunk_ids)).all()
        chunks_map = {c.id: c for c in chunks_db}

        candidate_chunks = []
        for cid in top_chunk_ids:
            chunk_obj = chunks_map.get(cid)
            if not chunk_obj or not chunk_obj.document:
                continue

            # Identify which retrieval method contributed
            has_semantic = cid in semantic_ranks
            has_keyword = cid in keyword_ranks
            if has_semantic and has_keyword:
                method = "Hybrid (Semantic + BM25)"
            elif has_semantic:
                method = "Semantic Vector"
            else:
                method = "BM25 Keyword"

            candidate_chunks.append({
                "chunk_id": chunk_obj.id,
                "document_id": chunk_obj.document_id,
                "document_name": chunk_obj.document.original_filename,
                "document_type": chunk_obj.document.file_type.upper(),
                "page_number": chunk_obj.page_number,
                "section_title": chunk_obj.section_title or f"Page {chunk_obj.page_number or 1}",
                "chunk_text": chunk_obj.chunk_text,
                "token_count": chunk_obj.token_count,
                "fused_score": fused_scores[cid],
                "semantic_rank": semantic_ranks.get(cid),
                "keyword_rank": keyword_ranks.get(cid),
                "retrieval_method": method
            })

        # 4. Cross-Encoder Reranking
        final_reranked = self.reranker.rerank(query, candidate_chunks, top_k=top_k)

        # Normalize relevance scores to a friendly 0.0 - 1.0 or percentage
        for item in final_reranked:
            raw = item.get("rerank_score", item.get("fused_score", 0.0))
            # Friendly score mapping
            score_normalized = min(1.0, max(0.1, (raw + 10.0) / 20.0 if raw < 0 else raw * 10.0 if raw < 0.1 else raw))
            item["relevance_score"] = round(score_normalized, 3)
            item["relevance_percentage"] = int(item["relevance_score"] * 100)

        return final_reranked
