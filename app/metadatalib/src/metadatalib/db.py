import datetime
import sys
from sqlalchemy import delete
from sqlalchemy.orm import Session
from . import SQLALCHEMY_DATABASE_URI
from .models import Annotation, Base, Project, Sample, Submission


def create_test_db(session: Session = None):
    if not session:
        from . import engine
        from . import session as imported_session

        if "sqlite" not in SQLALCHEMY_DATABASE_URI:
            print("Not a SQLite database, skipping test database creation.")
            sys.exit(1)

        session = imported_session
        Base.metadata.create_all(engine)

    if session.query(Project).count():
        session.execute(delete(Project))
        session.execute(delete(Submission))
        session.execute(delete(Sample))
        session.execute(delete(Annotation))

    p1 = Project(
        project_id=1,
        project_name="Test Project 1",
        contact_name="Test Contact 1",
        contact_email="test@test.edu",
        ticket_code="1",
    )
    p2 = Project(
        project_id=2,
        project_name="Test Project 2",
        contact_name="Test Contact 2",
        contact_email="test@test.edu",
        ticket_code="2",
    )
    session.bulk_save_objects([p1, p2])

    sub1 = Submission(
        submission_id=1,
        project_id=p1.project_id,
        version=1,
        comment="Test Comment 1",
        time_submitted=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
    )
    sub2 = Submission(
        submission_id=2,
        project_id=p2.project_id,
        version=1,
        comment="Test Comment 2",
        time_submitted=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
    )
    session.bulk_save_objects([sub1, sub2])

    s1 = Sample(
        sample_accession=1,
        sample_name="Test Sample 1",
        submission_id=sub1.submission_id,
        sample_type="Test Type 1",
        subject_id="Test Subject 1",
        host_species="Test Species 1",
    )
    s2 = Sample(
        sample_accession=2,
        sample_name="Test Sample 2",
        submission_id=sub1.submission_id,
        sample_type="Test Type 2",
        subject_id="Test Subject 2",
        host_species="Test Species 2",
    )
    s3 = Sample(
        sample_accession=3,
        sample_name="Test Sample 3",
        submission_id=sub2.submission_id,
        sample_type="Test Type 1",
        subject_id="Test Subject 3",
        host_species="Test Species 1",
    )
    session.bulk_save_objects([s1, s2, s3])

    a1 = Annotation(
        sample_accession=s1.sample_accession,
        attr="Test Attribute 1",
        val="Test Value 1",
    )
    a2 = Annotation(
        sample_accession=s1.sample_accession,
        attr="Test Attribute 2",
        val="Test Value 2",
    )
    a3 = Annotation(
        sample_accession=s2.sample_accession,
        attr="Test Attribute 1",
        val="Test Value 1",
    )
    a4 = Annotation(
        sample_accession=s2.sample_accession,
        attr="Test Attribute 2",
        val="Test Value 2",
    )
    session.bulk_save_objects([a1, a2, a3, a4])

    session.commit()
