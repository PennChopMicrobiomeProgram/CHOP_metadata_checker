import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from typing import Generator
from src.metadatalib.command import main
from src.metadatalib.db import create_test_db
from src.metadatalib.models import Base, Project


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    # This fixture should run before every test and create a new in-memory SQLite test database with identical data
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    create_test_db(session)

    yield session

    session.rollback()
    session.close()


def test_create_project(db):
    args = [
        "--project_name",
        "Test Project 3",
        "--customer_name",
        "Test Contact 3",
        "--customer_email",
        "test@test.edu",
    ]

    code = main(args, db)
    assert db.scalar(select(Project).filter(Project.ticket_code == code))
