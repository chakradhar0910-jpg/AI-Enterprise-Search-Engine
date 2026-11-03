from functools import wraps
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Department, Document, DocumentChunk, SearchHistory
from app.services.vector_store import VectorStore
from app.services.document_processor import DocumentProcessor

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    """Enforce strict administrator role check on the server side."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/")
@login_required
@admin_required
def admin_view():
    """Admin Control Center view."""
    users = User.query.order_by(User.id.asc()).all()
    documents = Document.query.order_by(Document.created_at.desc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()
    vector_store = VectorStore()

    stats = {
        "total_users": len(users),
        "total_documents": len(documents),
        "total_chunks": DocumentChunk.query.count(),
        "total_vectors": vector_store.total_vectors(),
        "total_queries": db.session.query(SearchHistory).count()
    }

    return render_template(
        "admin.html",
        users=users,
        documents=documents,
        departments=departments,
        stats=stats
    )


# API endpoints
@admin_bp.route("/api/admin/users", methods=["GET"])
@login_required
@admin_required
def api_admin_list_users():
    """List all registered users."""
    users = User.query.order_by(User.id.asc()).all()
    return jsonify({"success": True, "users": [u.to_dict() for u in users]})


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["PATCH"])
@login_required
@admin_required
def api_admin_update_user(user_id: int):
    """Update user role, active status, or department."""
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}

    if "role" in data:
        new_role = data["role"].lower()
        if new_role in ("admin", "user"):
            user.role = new_role

    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    if "department_id" in data:
        dept_id = data["department_id"]
        user.department_id = int(dept_id) if dept_id else None

    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()})


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@login_required
@admin_required
def api_admin_delete_user(user_id: int):
    """Delete a user account."""
    if user_id == current_user.id:
        return jsonify({"success": False, "error": "You cannot delete your own active administrator account."}), 400

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True, "message": f"User '{user.username}' deleted."})


@admin_bp.route("/api/admin/rebuild-index", methods=["POST"])
@login_required
@admin_required
def api_admin_rebuild_index():
    """Rebuild entire FAISS vector index and BM25 index from scratch."""
    from app.services.keyword_search import KeywordSearchService
    from app.services.embedding_service import EmbeddingService
    import faiss

    vector_store = VectorStore()
    embedding_service = EmbeddingService()
    keyword_service = KeywordSearchService()

    try:
        # Reset FAISS
        with vector_store._lock:
            base_index = faiss.IndexFlatIP(vector_store.dimension)
            vector_store.index = faiss.IndexIDMap(base_index)
            vector_store.metadata = {}
            vector_store._next_id = 0

        # Fetch all indexed documents
        indexed_docs = Document.query.filter_by(indexing_status="Indexed").all()
        reindexed_count = 0

        for doc in indexed_docs:
            chunks = doc.chunks.order_by(DocumentChunk.chunk_index.asc()).all()
            if not chunks:
                continue

            chunk_texts = [c.chunk_text for c in chunks]
            embeddings = embedding_service.encode(chunk_texts)

            chunks_meta = []
            bm25_items = []
            for c in chunks:
                chunks_meta.append({
                    "chunk_id": c.id,
                    "document_id": doc.id,
                    "department_id": doc.department_id,
                    "page_number": c.page_number,
                    "section_title": c.section_title
                })
                bm25_items.append({
                    "chunk_id": c.id,
                    "document_id": doc.id,
                    "chunk_text": c.chunk_text
                })

            faiss_ids = vector_store.add_vectors(embeddings, chunks_meta)
            for i, fid in enumerate(faiss_ids):
                chunks[i].embedding_id = fid

            reindexed_count += 1

        db.session.commit()

        # Rebuild BM25
        all_chunks = DocumentChunk.query.all()
        keyword_service.rebuild_index([
            {"chunk_id": c.id, "document_id": c.document_id, "chunk_text": c.chunk_text}
            for c in all_chunks
        ])

        return jsonify({
            "success": True,
            "message": f"Successfully rebuilt index across {reindexed_count} documents ({vector_store.total_vectors()} vectors)."
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Index rebuild failed: {str(e)}"}), 500
