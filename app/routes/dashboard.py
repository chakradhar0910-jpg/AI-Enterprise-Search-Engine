from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import Document, SearchHistory, User, Department, DocumentChunk
from app.services.vector_store import VectorStore

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def landing_page():
    """Public landing page presenting the AI Enterprise Search Engine platform."""
    return render_template("landing.html")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard_view():
    """Main authenticated analytics and control workspace."""
    # Query summary metrics
    if current_user.is_admin:
        total_docs = Document.query.count()
        indexed_docs = Document.query.filter_by(indexing_status="Indexed").count()
        total_queries = db.session.query(SearchHistory).count()
        total_users = User.query.count()
        recent_docs = Document.query.order_by(Document.created_at.desc()).limit(6).all()
        recent_searches = db.session.query(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(6).all()
    else:
        # Scoped to user's permitted documents
        user_dept = current_user.department_id
        doc_query = Document.query.filter(
            (Document.uploaded_by == current_user.id) |
            (Document.department_id == user_dept) |
            (Document.department_id.is_(None))
        )
        total_docs = doc_query.count()
        indexed_docs = doc_query.filter_by(indexing_status="Indexed").count()
        total_queries = db.session.query(SearchHistory).filter_by(user_id=current_user.id).count()
        total_users = None
        recent_docs = doc_query.order_by(Document.created_at.desc()).limit(6).all()
        recent_searches = db.session.query(SearchHistory).filter_by(user_id=current_user.id).order_by(SearchHistory.created_at.desc()).limit(6).all()

    vector_count = VectorStore().total_vectors()

    return render_template(
        "dashboard.html",
        total_docs=total_docs,
        indexed_docs=indexed_docs,
        total_queries=total_queries,
        total_users=total_users,
        vector_count=vector_count,
        recent_docs=recent_docs,
        recent_searches=recent_searches
    )


@dashboard_bp.route("/api/dashboard/stats")
@login_required
def api_stats():
    """Return JSON statistics for Chart.js and dynamic updates."""
    # 1. Document Type Distribution
    type_counts = dict(
        db.session.query(Document.file_type, func.count(Document.id))
        .group_by(Document.file_type)
        .all()
    )
    # Normalize labels
    dist_labels = ["PDF", "DOCX", "TXT"]
    dist_data = [
        type_counts.get("pdf", 0),
        type_counts.get("docx", 0),
        type_counts.get("txt", 0)
    ]

    # 2. Search Activity Over Past 7 Days
    seven_days_ago = datetime.utcnow() - timedelta(days=6)
    activity_labels = []
    activity_counts = []

    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

        if current_user.is_admin:
            cnt = db.session.query(SearchHistory).filter(
                SearchHistory.created_at >= day_start,
                SearchHistory.created_at <= day_end
            ).count()
        else:
            cnt = db.session.query(SearchHistory).filter(
                SearchHistory.user_id == current_user.id,
                SearchHistory.created_at >= day_start,
                SearchHistory.created_at <= day_end
            ).count()

        activity_labels.append(day.strftime("%b %d"))
        activity_counts.append(cnt)

    # 3. Overall counts
    total_docs = Document.query.count() if current_user.is_admin else Document.query.filter(
        (Document.uploaded_by == current_user.id) | (Document.department_id == current_user.department_id)
    ).count()
    indexed_docs = Document.query.filter_by(indexing_status="Indexed").count()

    return jsonify({
        "total_documents": total_docs,
        "indexed_documents": indexed_docs,
        "total_queries": db.session.query(SearchHistory).count() if current_user.is_admin else db.session.query(SearchHistory).filter_by(user_id=current_user.id).count(),
        "total_users": User.query.count() if current_user.is_admin else None,
        "total_vectors": VectorStore().total_vectors(),
        "type_distribution": {
            "labels": dist_labels,
            "data": dist_data
        },
        "search_activity": {
            "labels": activity_labels,
            "data": activity_counts
        }
    })
