import os
import shutil
import tempfile
from pathlib import Path
import numpy as np
import pytest
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.keyword_search import KeywordSearchService
from app.services.reranker import RerankerService
from app.services.llm_service import LLMService


def test_embedding_generation():
    """Verify SentenceTransformer embeddings produce normalized 384-dimensional vectors."""
    service = EmbeddingService()
    texts = [
        "Employees can request annual leave through the HR portal.",
        "How can I apply for vacation?"
    ]
    embeddings = service.encode(texts)
    assert embeddings.shape == (2, 384)
    assert embeddings.dtype == np.float32

    # Check vector normalization (L2 norm ≈ 1.0)
    norm1 = np.linalg.norm(embeddings[0])
    norm2 = np.linalg.norm(embeddings[1])
    assert abs(norm1 - 1.0) < 1e-4
    assert abs(norm2 - 1.0) < 1e-4

    # Semantic similarity check: both statements share positive semantic similarity
    cosine_sim = np.dot(embeddings[0], embeddings[1])
    assert cosine_sim > 0.25, f"Expected positive semantic similarity, got {cosine_sim}"


def test_faiss_vector_store():
    """Verify FAISS vector store adding, searching, and document purging."""
    temp_dir = tempfile.mkdtemp()
    try:
        vs = VectorStore(index_dir=temp_dir, dimension=384)
        emb_service = EmbeddingService()

        chunks_text = [
            "Company laptops must be secured with BitLocker disk encryption.",
            "Work from home policy allows two days remote per week."
        ]
        embeddings = emb_service.encode(chunks_text)

        chunks_meta = [
            {"chunk_id": 101, "document_id": 1, "department_id": 1, "page_number": 1, "section_title": "IT Security"},
            {"chunk_id": 102, "document_id": 2, "department_id": 2, "page_number": 2, "section_title": "Remote Work"}
        ]

        assigned_ids = vs.add_vectors(embeddings, chunks_meta)
        assert len(assigned_ids) == 2
        assert vs.total_vectors() == 2

        # Query for IT Security
        q_emb = emb_service.encode_query("encryption on corporate laptops")
        results = vs.search(q_emb, top_k=1)
        assert len(results) == 1
        assert results[0]["chunk_id"] == 101
        assert results[0]["similarity"] > 0.4

        # Remove Document 1
        removed = vs.remove_document_vectors(document_id=1)
        assert removed == 1
        assert vs.total_vectors() == 1

        # Search again: Document 1 chunk should not be returned
        results_after = vs.search(q_emb, top_k=2)
        assert len(results_after) == 1
        assert results_after[0]["chunk_id"] == 102
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_bm25_keyword_search():
    """Verify BM25 keyword matching for exact terms, names, and numbers."""
    bm25_service = KeywordSearchService()
    chunks = [
        {"chunk_id": 1, "document_id": 10, "chunk_text": "Project Apollo release date is scheduled for October 15, 2026."},
        {"chunk_id": 2, "document_id": 11, "chunk_text": "Expense reports must be filed within 30 days of travel."}
    ]
    bm25_service.rebuild_index(chunks)

    # Search exact entity
    res = bm25_service.search("Apollo release date", top_k=1)
    assert len(res) == 1
    assert res[0]["chunk_id"] == 1
    assert res[0]["score"] > 0.0


def test_cross_encoder_reranker():
    """Verify Cross-Encoder reranking ranks the most relevant passage on top."""
    reranker = RerankerService()
    query = "How do I report an IT incident?"
    candidates = [
        {"chunk_id": 1, "chunk_text": "The cafeteria menu changes every Monday.", "fused_score": 0.5},
        {"chunk_id": 2, "chunk_text": "To report an IT incident, open a ticket at helpdesk.company.com or dial extension 4357.", "fused_score": 0.4}
    ]
    reranked = reranker.rerank(query, candidates, top_k=2)
    assert len(reranked) == 2
    # The IT incident chunk must be ranked first
    assert reranked[0]["chunk_id"] == 2


def test_rag_llm_grounded_synthesis():
    """Verify LLMService provides grounded factual answers and attaches source references."""
    llm = LLMService()
    query = "What is the Wi-Fi password?"
    chunks = [
        {
            "chunk_id": 1,
            "document_id": 5,
            "document_name": "Office Guide.pdf",
            "page_number": 2,
            "section_title": "Network Access",
            "chunk_text": "The corporate Wi-Fi network is Enterprise-Secure. Guest Wi-Fi password is Guest2026."
        }
    ]

    res = llm.generate_answer(query, chunks)
    assert "answer" in res
    assert len(res["sources"]) == 1
    assert res["sources"][0]["document_name"] == "Office Guide.pdf"
    assert res["sources"][0]["page_number"] == 2
    assert "Guest2026" in res["answer"]
