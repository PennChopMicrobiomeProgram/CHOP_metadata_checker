from pathlib import Path
from src.metadatalib import SQLALCHEMY_DATABASE_URI
from src.metadatalib.db import create_test_db


def test_create_test_db():
    create_test_db()
    assert Path(SQLALCHEMY_DATABASE_URI[10:]).exists()
