from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os
import atexit
from contextlib import contextmanager

load_dotenv()

# Global engine variable
_engine = None

def get_engine():
    """
    Create database engine only once.
    If engine already exists, reuse it.
    """
    global _engine

    if _engine is None:
        # Use the DB_KEY from environment (e.g., postgresql://user:pass@host/db) : JD
        db_key = os.getenv("DB_KEY")
        if not db_key:
            raise ValueError("DB_KEY environment variable not set")
        _engine = create_engine(db_key)
        print("✅ Database engine created successfully...")

        # Register cleanup when Python process ends
        atexit.register(close_engine)

    return _engine

def close_engine():
    """
    Dispose the database engine when program finishes.
    """
    global _engine

    if _engine is not None:
        _engine.dispose()
        print("✅ Database engine disposed successfully...")
        _engine = None

# @contextmanager
def get_session():
    """
    Create a session for database operations.

    - Opens engine if needed
    - Creates a new session
    - Commits if success
    - Rollback if error
    - Closes session always
    """
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False)
    session = SessionLocal()

    try:
        print("✅ Session object created successfully...")
        yield session
        session.commit()
        print("✅ Transaction committed successfully...")
    except Exception:
        session.rollback()
        print("❌ Transaction rolled back due to error...")
        raise
    finally:
        session.close()
        print("✅ Session closed successfully...")