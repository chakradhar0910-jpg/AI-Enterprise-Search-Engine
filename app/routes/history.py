from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import SearchHistory

history_bp = Blueprint("history", __name__)


@history_bp.route("/")
@login_required
def history_view():
    """Search history page displaying previous queries and grounded citations."""
    histories = (
        db.session.query(SearchHistory)
        .filter_by(user_id=current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .all()
    )
    return render_template("history.html", histories=histories)


@history_bp.route("/api/search/history", methods=["GET"])
@login_required
def api_get_history():
    """Retrieve JSON search history records."""
    histories = (
        db.session.query(SearchHistory)
        .filter_by(user_id=current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .all()
    )
    return jsonify({"success": True, "history": [h.to_dict() for h in histories]})


@history_bp.route("/api/search/history/<int:history_id>", methods=["DELETE"])
@login_required
def api_delete_history_item(history_id: int):
    """Delete an individual history record."""
    item = db.session.query(SearchHistory).filter_by(id=history_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"success": True, "message": "History item deleted."})


@history_bp.route("/api/search/history/clear", methods=["POST"])
@login_required
def api_clear_history():
    """Clear all search history for current user."""
    db.session.query(SearchHistory).filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True, "message": "Search history cleared."})
