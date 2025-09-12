from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tablemusthave import Table

from metadatalib.db import create_test_db
from metadatalib.models import Base, Annotation, Sample
from metadatalib.utils import (
    export_table,
    get_nullable_field,
    import_table,
    is_importable,
)


class DummyDB:
    def __init__(self, session):
        self.session = session


@pytest.fixture()
def db() -> Generator[DummyDB, None, None]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    create_test_db(session)
    yield DummyDB(session)
    session.rollback()
    session.close()


def test_get_nullable_field_handles_index_error():
    t = Table(["SampleID"], [["s1"], ["s2"]])
    assert get_nullable_field(t, 0, "SampleID") == "s1"
    assert get_nullable_field(t, 5, "SampleID") is None


def test_is_importable_checks_mandatory_columns():
    good = Table(
        ["SampleID", "investigator", "sample_type"],
        [["s1", "inv", "type"]],
    )
    bad = Table(["SampleID", "sample_type"], [["s1", "type"]])
    assert is_importable(good)
    assert not is_importable(bad)


def test_import_and_export_table_round_trip(db):
    t = Table(
        [
            "SampleID",
            "sample_type",
            "subject_id",
            "host_species",
            "investigator",
            "extra_attr",
        ],
        [
            [
                "SampleA",
                "Type1",
                "Subject1",
                "Species1",
                "Investigator1",
                "Extra1",
            ],
            [
                "SampleB",
                "Type2",
                "Subject2",
                "Species2",
                "Investigator2",
                "Extra2",
            ],
        ],
    )

    submission = import_table(t, db, project_code="1", comment="test")
    # two new samples with two annotation columns each
    samples = (
        db.session.query(Sample).filter_by(submission_id=submission.submission_id).all()
    )
    assert len(samples) == 2
    annotations = (
        db.session.query(Annotation)
        .filter(Annotation.sample_accession.in_([s.sample_accession for s in samples]))
        .all()
    )
    assert len(annotations) == 4

    exported = export_table(db, submission.submission_id)
    assert exported.colnames()[:4] == t.colnames()[:4]
    assert set(exported.colnames()) == set(t.colnames())
    for col in t.colnames():
        assert exported.get(col) == t.get(col)
