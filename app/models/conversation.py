import json
import uuid
from datetime import datetime
from app.extensions import db


class Conversation(db.Model):
    """Conversation model representing a multi-turn RAG chat session."""
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(128), default="New Enterprise Chat", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="conversations")
    messages = db.relationship("Message", back_populates="conversation", cascade="all, delete-orphan", lazy="dynamic", order_by="Message.created_at.asc()")

    def to_dict(self, include_messages: bool = False) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message_count": self.messages.count()
        }
        if include_messages:
            data["messages"] = [m.to_dict() for m in self.messages.all()]
        return data

    def __repr__(self):
        return f"<Conversation {self.id} '{self.title}'>"


class Message(db.Model):
    """Message model representing each individual exchange in a RAG conversation."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String(16), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    sources_json = db.Column(db.Text, nullable=True)  # JSON-encoded array of retrieved source references
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = db.relationship("Conversation", back_populates="messages")

    @property
    def sources(self) -> list:
        """Parse source references from JSON."""
        if not self.sources_json:
            return []
        try:
            return json.loads(self.sources_json)
        except Exception:
            return []

    @sources.setter
    def sources(self, value: list) -> None:
        """Serialize source references to JSON."""
        self.sources_json = json.dumps(value, ensure_ascii=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __repr__(self):
        return f"<Message {self.id} [{self.role}] Conv:{self.conversation_id}>"
