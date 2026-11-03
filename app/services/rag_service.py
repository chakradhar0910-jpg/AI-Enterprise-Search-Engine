from typing import List, Dict, Any, Optional
from app.extensions import db
from app.models import User, SearchHistory
from app.services.hybrid_retrieval import HybridRetriever
from app.services.llm_service import LLMService


class RAGService:
    """End-to-end orchestration service for Hybrid Retrieval-Augmented Generation."""

    def __init__(self):
        self.retriever = HybridRetriever()
        self.llm = LLMService()

    def search_and_generate(
        self,
        query: str,
        user: User,
        top_k: int = 5,
        search_mode: str = "hybrid",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        save_history: bool = True
    ) -> Dict[str, Any]:
        """
        Execute RAG Pipeline:
        1. Query validation
        2. Permission-checked hybrid retrieval
        3. LLM answer synthesis
        4. Grounded source attribution
        5. Search history tracking
        """
        query_clean = query.strip()
        if not query_clean:
            return {
                "success": False,
                "error": "Query cannot be empty.",
                "answer": "",
                "sources": []
            }

        # 1. Retrieve relevant chunks with permissions and reranking
        retrieved_chunks = self.retriever.retrieve(
            query=query_clean,
            user=user,
            top_k=top_k,
            search_mode=search_mode
        )

        # 2. Synthesize answer with LLM / grounded synthesizer
        generation_res = self.llm.generate_answer(
            query=query_clean,
            retrieved_chunks=retrieved_chunks,
            conversation_history=conversation_history
        )

        answer = generation_res.get("answer", "")
        sources = generation_res.get("sources", [])
        provider = generation_res.get("provider", "RAG Engine")
        model = generation_res.get("model", "default")

        # 3. Save Search History
        if save_history and user and user.is_authenticated:
            try:
                unique_doc_names = list(set([s["document_name"] for s in sources]))
                history_entry = SearchHistory(
                    user_id=user.id,
                    query_text=query_clean,
                    results_count=len(retrieved_chunks),
                    retrieval_method=search_mode.capitalize() + (" (RRF + Rerank)" if search_mode == "hybrid" else ""),
                    answer_snippet=answer[:250] + ("..." if len(answer) > 250 else ""),
                    source_documents=", ".join(unique_doc_names) if unique_doc_names else None
                )
                db.session.add(history_entry)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"[RAGService] Notice saving search history: {e}")

        return {
            "success": True,
            "query": query_clean,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": retrieved_chunks,
            "total_retrieved": len(retrieved_chunks),
            "search_mode": search_mode,
            "provider": provider,
            "model": model,
            "sufficient_evidence": generation_res.get("sufficient_evidence", True)
        }
