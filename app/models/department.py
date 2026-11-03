from datetime import datetime
from app.extensions import db


class Department(db.Model):
    """Department model for organizational scoping and access control."""
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    users = db.relationship("User", back_populates="department")
    documents = db.relationship("Document", back_populates="department")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "user_count": len(self.users),
            "document_count": len(self.documents),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __repr__(self):
        return f"<Department {self.name}>"
