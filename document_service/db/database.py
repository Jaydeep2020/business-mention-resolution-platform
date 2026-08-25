import atexit

from sqlalchemy import (
    create_engine,
)

from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from document_service.core.config import (
    settings,
)


_engine = None


def get_engine():

    global _engine

    if _engine is None:

        _engine = create_engine(
            settings.DOCUMENT_DB_KEY,
            pool_pre_ping=True,
        )

        atexit.register(
            close_engine
        )

    return _engine


def close_engine():

    global _engine

    if _engine is not None:

        _engine.dispose()

        _engine = None


def get_session():

    SessionLocal = sessionmaker(
        bind=get_engine(),
        autoflush=False,
        expire_on_commit=False,
    )

    session: Session = (
        SessionLocal()
    )

    try:

        yield session

        session.commit()

    except Exception:

        session.rollback()

        raise

    finally:

        session.close()