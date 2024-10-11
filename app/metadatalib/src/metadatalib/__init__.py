import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


__version__ = "0.2.0"

try:
    db_host = os.environ["METADATA_DB_HOST"]
    db_user = os.environ["METADATA_DB_USER"]
    db_name = os.environ["METADATA_DB_NAME"]
    db_pswd = os.environ["METADATA_DB_PSWD"]
    SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_pswd}@{db_host}/{db_name}"
except KeyError:
    sys.stderr.write(
        "Missing database connection information in environment, using test SQLite database.\n"
    )
    sys.stderr.write(
        f"METADATA_DB_HOST: {os.environ.get('METADATA_DB_HOST')}\nMETADATA_DB_USER: {os.environ.get('METADATA_DB_USER')}\nMETADATA_DB_NAME: {os.environ.get('METADATA_DB_NAME')}\nMETADATA_DB_PSWD: {os.environ.get('METADATA_DB_PSWD')}\n"
    )
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{Path(__file__).parent.parent.parent.parent.parent.resolve()}/metadata.sqlite3"

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
except SQLAlchemyError as e:
    # Need to do handling here
    raise e
    session = None
