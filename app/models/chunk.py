from datetime import datetime
from app.extensions import db


class DocumentChunk(db.Model):
    """DocumentChunk model storing chunked textual units with metadata for retrieval."""
    __tablename__ = "document_chunks"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    page_number = db.Column(db.Integer, nullable=True)
    section_title = db.Column(db.String(255), nullable=True)
    token_count = db.Column(db.Integer, default=0, nullable=False)
    embedding_id = db.Column(db.Integer, nullable=True, index=True)  # Vector ID in FAISS index
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = db.relationship("Document", back_populates="chunks")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "document_name": self.document.original_filename if self.document else "Unknown",
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "token_count": self.token_count,
            "embedding_id": self.embedding_id
        }

    def __repr__(self):
        return f"<DocumentChunk Doc:{self.document_id} Chk:{self.chunk_index} Pg:{self.page_number}>"
