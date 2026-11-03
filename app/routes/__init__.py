from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.documents import documents_bp
from app.routes.search import search_bp
from app.routes.chat import chat_bp
from app.routes.history import history_bp
from app.routes.admin import admin_bp

__all__ = [
    "auth_bp",
    "dashboard_bp",
    "documents_bp",
    "search_bp",
    "chat_bp",
    "history_bp",
    "admin_bp",
]
