from datetime import datetime
from app.extensions import db


class Document(db.Model):
    """Document model representing uploaded enterprise files."""
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, unique=True, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(16), nullable=False)  # 'pdf', 'docx', 'txt'
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    # Processing and Indexing State
    processing_status = db.Column(db.String(32), default="Uploaded", nullable=False)  # Uploaded, Processing, Indexed, Failed
    indexing_status = db.Column(db.String(32), default="Pending", nullable=False)     # Pending, Indexed, Failed
    error_message = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    page_count = db.Column(db.Integer, default=0, nullable=False)
    chunk_count = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    uploader = db.relationship("User", back_populates="documents")
    department = db.relationship("Department", back_populates="documents")
    chunks = db.relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", lazy="dynamic")
    permissions = db.relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def formatted_size(self) -> str:
        """Return human-readable file size string."""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type.upper(),
            "file_size": self.file_size,
            "formatted_size": self.formatted_size,
            "uploaded_by": self.uploader.username if self.uploader else "Unknown",
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else "All Departments",
            "processing_status": self.processing_status,
            "indexing_status": self.indexing_status,
            "error_message": self.error_message,
            "summary": self.summary,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }

    def __repr__(self):
        return f"<Document {self.original_filename} ({self.processing_status})>"


class DocumentPermission(db.Model):
    """Access control permission link between documents and departments."""
    __tablename__ = "document_permissions"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    document = db.relationship("Document", back_populates="permissions")
    department = db.relationship("Department")
