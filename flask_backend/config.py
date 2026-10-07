import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env")


class Config:
    SECRET_KEY = (
        os.environ.get("SECRET_KEY")
        or os.environ.get("DJANGO_SECRET_KEY")
        or "wingroo-flask-secret-key-2026"
    )

    db_user = os.environ.get("DB_USER", "wingroo")
    db_pass = os.environ.get("DB_PASSWORD", "")
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_port = os.environ.get("DB_PORT", "3306")
    db_name = os.environ.get("DB_NAME", "internship_certificate_db")

    if db_pass:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        )
    else:
        instance_dir = BASE_DIR / "instance"
        instance_dir.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = (
            os.environ.get("DATABASE_URL")
            or f"sqlite:///{instance_dir / 'certificate.db'}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Media folder for uploads & generated certificate PDFs
    MEDIA_FOLDER = os.environ.get("MEDIA_FOLDER") or str(
        PROJECT_ROOT / "backend" / "media"
    )
    ASSETS_FOLDER = os.environ.get("ASSETS_FOLDER") or str(
        PROJECT_ROOT / "assets"
    )

    FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://127.0.0.1:5174")

    # CORS origins
    CORS_ALLOWED_ORIGINS = os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5174,http://127.0.0.1:5174,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")

    JWT_EXPIRATION_HOURS = 24
