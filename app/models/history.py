from datetime import datetime
from app.extensions import db


class SearchHistory(db.Model):
    """SearchHistory model storing historical search queries and generated summaries."""
    __tablename__ = "search_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    query_text = db.Column(db.Text, nullable=False)
    results_count = db.Column(db.Integer, default=0, nullable=False)
    retrieval_method = db.Column(db.String(64), default="Hybrid (Semantic + BM25)", nullable=False)
    answer_snippet = db.Column(db.Text, nullable=True)
    source_documents = db.Column(db.Text, nullable=True)  # Comma-separated list of source document names
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = db.relationship("User", back_populates="search_history")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "query": self.query_text,
            "query_text": self.query_text,
            "results_count": self.results_count,
            "retrieval_method": self.retrieval_method,
            "answer_snippet": self.answer_snippet,
            "source_documents": self.source_documents.split(", ") if self.source_documents else [],
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __repr__(self):
        return f"<SearchHistory User:{self.user_id} Query:'{self.query_text[:30]}'>"
