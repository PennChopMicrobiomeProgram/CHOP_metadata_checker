import os
from pathlib import Path


def get_database_uri() -> str:
    return os.environ.get(
        "METADATA_DB_URI",
        f"sqlite:///{Path(__file__).resolve().parent.parent / 'metadata.sqlite3'}",
    )
