from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from metadatalib.config import get_database_uri

_ENGINE = None
_SESSION = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(get_database_uri())
    return _ENGINE


def get_session() -> Session:
    global _SESSION
    if _SESSION is None:
        try:
            engine = get_engine()
            SessionLocal = sessionmaker(bind=engine)
            _SESSION = SessionLocal()
        except SQLAlchemyError as exc:
            raise SQLAlchemyError(
                f"Error connecting to database: {get_database_uri()}"
            ) from exc
    return _SESSION
