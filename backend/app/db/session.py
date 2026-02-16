"""
Database session management with connection pooling for SQLite.
Configures SQLAlchemy engine with WAL mode and connection pooling.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


# Global engine and session factory
_engine: Engine = None
_SessionLocal: sessionmaker = None


def init_database() -> None:
    """
    Initialize database engine and session factory.
    Configures SQLite with WAL mode and foreign key support.
    """
    global _engine, _SessionLocal

    # Create engine with connection pooling
    # For SQLite, use StaticPool to maintain single connection in memory
    _engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},  # Allow multi-threaded access
        poolclass=StaticPool,  # Single connection pool for SQLite
        echo=settings.log_level == "debug",  # Log SQL queries in debug mode
    )

    # Configure SQLite pragmas on each connection
    @event.listens_for(_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite pragmas for each new connection."""
        cursor = dbapi_conn.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        # Enable WAL mode for better concurrency (T022)
        cursor.execute("PRAGMA journal_mode = WAL")
        # Optimize for performance
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
        cursor.execute("PRAGMA temp_store = MEMORY")
        cursor.close()

    # Create session factory
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
    )


def get_engine() -> Engine:
    """
    Get the global database engine.

    Returns:
        SQLAlchemy Engine instance

    Raises:
        RuntimeError: If database not initialized
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get the global session factory.

    Returns:
        SQLAlchemy sessionmaker

    Raises:
        RuntimeError: If database not initialized
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Automatically commits on success, rolls back on error.

    Yields:
        SQLAlchemy Session

    Example:
        with get_db_session() as db:
            assistant = db.query(Assistant).first()
    """
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection function for FastAPI.
    Provides database session to route handlers.

    Yields:
        SQLAlchemy Session

    Example:
        @app.get("/assistants")
        def list_assistants(db: Session = Depends(get_db)):
            return db.query(Assistant).all()
    """
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def close_database() -> None:
    """
    Close database connections and dispose of engine.
    Should be called on application shutdown.
    """
    global _engine
    if _engine:
        _engine.dispose()
        _engine = None
