import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DB_DIR = BASE_DIR / "db"
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"


def _default_database_url() -> str:
    database_path = (DB_DIR / "app.db").resolve().as_posix()
    return f"sqlite:///{database_path}"


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


APP_NAME = os.getenv("APP_NAME", "Bank Statement Portal")
DATABASE_URL = os.getenv("DATABASE_URL", _default_database_url())
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "bank_portal_session")
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))
SESSION_SECURE_COOKIE = _as_bool(os.getenv("SESSION_SECURE_COOKIE"), default=False)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
MAX_UPLOAD_FILES = int(os.getenv("MAX_UPLOAD_FILES", "10"))
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_LENGTH = 8
ALLOWED_EXTENSIONS = {".pdf"}
