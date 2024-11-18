import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


__version__ = "0.2.0"

try:
    SQLALCHEMY_DATABASE_URI = os.environ["METADATA_DB_URI"]
except KeyError:
    sys.stderr.write(
        "Missing METADATA_DB_URI in environment, using test SQLite database.\n"
    )
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{Path(__file__).parent.parent.parent.parent.parent.resolve()}/metadata.sqlite3"

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
except SQLAlchemyError as e:
    # Need to do handling here
    sys.stderr.write(f"Error connecting to database: {SQLALCHEMY_DATABASE_URI}\n")
    raise e
    session = None
