from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    """User account model for enterprise authentication and authorization."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)  # 'admin' or 'user'
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    department = db.relationship("Department", back_populates="users")
    documents = db.relationship("Document", back_populates="uploader", lazy="dynamic")
    search_history = db.relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    conversations = db.relationship("Conversation", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Hash and store the password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        """Check if user has administrative privileges."""
        return self.role.lower() == "admin"

    def to_dict(self) -> dict:
        """Serialize user object to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else "General / None",
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
