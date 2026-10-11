"""
Database Engine & Session Dependency Injection
Configured for SQLite local development and PostgreSQL production deployment.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

# Handle SQLite vs PostgreSQL URL specifics
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Ensure directory exists for sqlite file
    if "///" in settings.DATABASE_URL:
        db_file = settings.DATABASE_URL.split("///")[-1]
        os.makedirs(os.path.dirname(os.path.abspath(db_file)), exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency injection generator yielding an active SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
