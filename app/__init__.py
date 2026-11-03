import os
from pathlib import Path
from flask import Flask, render_template, redirect, url_for
from app.config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    """Application factory for AI Enterprise Search Engine."""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    # Ensure storage paths exist
    for folder in [app.config["UPLOAD_FOLDER"], app.config["PROCESSED_FOLDER"], app.config["VECTOR_STORE_DIR"]]:
        Path(folder).mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User, Department, Document, DocumentChunk

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.documents import documents_bp
    from app.routes.search import search_bp
    from app.routes.chat import chat_bp
    from app.routes.history import history_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(documents_bp, url_prefix="/documents")
    app.register_blueprint(search_bp, url_prefix="/search")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(history_bp, url_prefix="/history")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Global template context processors
    @app.context_processor
    def inject_app_metadata():
        return {
            "app_name": "CognitiveSearch Enterprise",
            "app_version": "1.0.0",
            "llm_provider": app.config.get("LLM_PROVIDER", "groq").upper()
        }

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def access_forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    # Initialize database and default records
    with app.app_context():
        db.create_all()
        _seed_initial_data()
        _init_bm25_from_db()

    return app


def _seed_initial_data():
    """Seed initial departments and default admin/user accounts if empty."""
    from app.models import Department, User

    # 1. Seed Departments
    initial_departments = [
        {"name": "Human Resources", "description": "HR policies, benefits, leave and employee relations."},
        {"name": "Engineering & Technology", "description": "Software architecture, DevOps, APIs and technical specifications."},
        {"name": "Legal & Compliance", "description": "Enterprise compliance, vendor contracts, security and NDAs."},
        {"name": "Product & Operations", "description": "Product roadmaps, sprint planning and operations manuals."},
        {"name": "General Enterprise", "description": "Company-wide general announcements and cross-departmental documentation."}
    ]

    for dept_data in initial_departments:
        if not Department.query.filter_by(name=dept_data["name"]).first():
            dept = Department(name=dept_data["name"], description=dept_data["description"])
            db.session.add(dept)

    db.session.commit()

    hr_dept = Department.query.filter_by(name="Human Resources").first()
    eng_dept = Department.query.filter_by(name="Engineering & Technology").first()

    # 2. Seed Default Administrator
    admin = User.query.filter_by(email="admin@enterprise.ai").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@enterprise.ai",
            role="admin",
            department_id=eng_dept.id if eng_dept else None,
            is_active=True
        )
        admin.set_password("Admin@123456")
        db.session.add(admin)

    # 3. Seed Default Regular User
    regular_user = User.query.filter_by(email="user@enterprise.ai").first()
    if not regular_user:
        regular_user = User(
            username="john_doe",
            email="user@enterprise.ai",
            role="user",
            department_id=hr_dept.id if hr_dept else None,
            is_active=True
        )
        regular_user.set_password("User@123456")
        db.session.add(regular_user)

    db.session.commit()


def _init_bm25_from_db():
    """Load existing chunks from database into BM25 index on startup."""
    try:
        from app.models import DocumentChunk
        from app.services.keyword_search import KeywordSearchService
        chunks = DocumentChunk.query.all()
        if chunks:
            chunk_payloads = [
                {"chunk_id": c.id, "document_id": c.document_id, "chunk_text": c.chunk_text}
                for c in chunks
            ]
            KeywordSearchService().rebuild_index(chunk_payloads)
    except Exception as e:
        print(f"[Init] BM25 startup notice: {e}")
