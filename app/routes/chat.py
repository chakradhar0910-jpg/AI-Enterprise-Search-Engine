import uuid
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Conversation, Message
from app.services.rag_service import RAGService

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
@login_required
def chat_view():
    """RAG conversational AI assistant interface."""
    conversations = (
        Conversation.query.filter_by(user_id=current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return render_template("chat.html", conversations=conversations)


# API endpoints
@chat_bp.route("/api/chat/conversations", methods=["GET"])
@login_required
def api_list_conversations():
    """List all chat sessions for the logged-in user."""
    convs = (
        Conversation.query.filter_by(user_id=current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return jsonify({"success": True, "conversations": [c.to_dict() for c in convs]})


@chat_bp.route("/api/chat/conversations", methods=["POST"])
@login_required
def api_create_conversation():
    """Create a new conversational thread."""
    data = request.get_json() or {}
    title = data.get("title", "New Enterprise Chat").strip() or "New Enterprise Chat"

    conv = Conversation(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=title[:100]
    )
    db.session.add(conv)
    db.session.commit()
    return jsonify({"success": True, "conversation": conv.to_dict()}), 201


@chat_bp.route("/api/chat/conversations/<string:conv_id>", methods=["GET"])
@login_required
def api_get_conversation(conv_id: str):
    """Retrieve messages and sources for a conversation."""
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    return jsonify({"success": True, "conversation": conv.to_dict(include_messages=True)})


@chat_bp.route("/api/chat/conversations/<string:conv_id>/messages", methods=["POST"])
@login_required
def api_send_message(conv_id: str):
    """Post user message, run RAG hybrid retrieval & LLM generation, store response with source attribution."""
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}
    user_content = data.get("message", "").strip()

    if not user_content:
        return jsonify({"success": False, "error": "Message cannot be empty."}), 400

    # 1. Save user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=user_content
    )
    db.session.add(user_msg)
    db.session.commit()

    # Update conversation title if it was default
    if conv.title == "New Enterprise Chat":
        conv.title = user_content[:45] + ("..." if len(user_content) > 45 else "")
        db.session.commit()

    # 2. Gather conversation history for context
    history_messages = [
        {"role": m.role, "content": m.content}
        for m in conv.messages.order_by(Message.created_at.asc()).all()[-6:]
    ]

    # 3. Run RAG Pipeline
    rag_service = RAGService()
    rag_res = rag_service.search_and_generate(
        query=user_content,
        user=current_user,
        top_k=5,
        search_mode="hybrid",
        conversation_history=history_messages,
        save_history=True
    )

    assistant_answer = rag_res.get("answer", "")
    sources = rag_res.get("sources", [])

    # 4. Save assistant response with sources
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=assistant_answer
    )
    assistant_msg.sources = sources
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        "success": True,
        "user_message": user_msg.to_dict(),
        "assistant_message": assistant_msg.to_dict(),
        "sources": sources
    })


@chat_bp.route("/api/chat/conversations/<string:conv_id>", methods=["DELETE"])
@login_required
def api_delete_conversation(conv_id: str):
    """Delete conversation session and all its messages."""
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    db.session.delete(conv)
    db.session.commit()
    return jsonify({"success": True, "message": "Conversation deleted."})
