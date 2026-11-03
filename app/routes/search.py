from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.rag_service import RAGService

search_bp = Blueprint("search", __name__)


@search_bp.route("/")
@login_required
def search_view():
    """Natural Language AI Search interface with suggestions and filters."""
    query = request.args.get("q", "").strip()
    mode = request.args.get("mode", "hybrid").lower()
    return render_template("search.html", initial_query=query, initial_mode=mode)


@search_bp.route("/api/search", methods=["POST"])
@login_required
def api_search():
    """Execute enterprise search and RAG synthesis with source attribution."""
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    mode = data.get("mode", "hybrid").lower()
    top_k = int(data.get("top_k", 5))

    if not query:
        return jsonify({"success": False, "error": "Search query cannot be empty."}), 400

    if mode not in ("hybrid", "semantic", "keyword"):
        mode = "hybrid"

    rag_service = RAGService()
    result = rag_service.search_and_generate(
        query=query,
        user=current_user,
        top_k=top_k,
        search_mode=mode,
        save_history=True
    )

    return jsonify(result)
