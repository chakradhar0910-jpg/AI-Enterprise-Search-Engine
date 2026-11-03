import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base configuration settings for Enterprise Search Engine."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-enterprise-search-secret-key-xyz-987")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'enterprise_search.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Directories
    BASE_DIR = BASE_DIR
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "data/uploads")
    PROCESSED_FOLDER = BASE_DIR / os.getenv("PROCESSED_FOLDER", "data/processed")
    VECTOR_STORE_DIR = BASE_DIR / os.getenv("VECTOR_STORE_DIR", "data/vector_store")

    # Upload constraints
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB maximum file size
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

    # AI & NLP Settings
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    RERANKER_MODEL_NAME = os.getenv("RERANKER_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))

    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()


class TestConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
