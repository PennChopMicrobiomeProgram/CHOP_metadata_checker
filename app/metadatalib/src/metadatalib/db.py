import datetime
import sys
from pathlib import Path
from . import engine, session, SQLALCHEMY_DATABASE_URI
from .models import Annotation, Base, Project, Sample, Submission


def create_test_db():
    print(SQLALCHEMY_DATABASE_URI)
    if "sqlite" not in SQLALCHEMY_DATABASE_URI:
        print("Not a SQLite database, skipping test database creation.")
        sys.exit(1)
    if Path(SQLALCHEMY_DATABASE_URI[10:]).exists():
        print("Test database already exists, skipping test database creation.")
        sys.exit(1)

    Base.metadata.create_all(engine)

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


class MetadataDB(object):
    def __init__(self, host, user, password, db_name):
        self.conn = psycopg2.connect(
            host=host, user=user, password=password, dbname=db_name, port="5432"
        )

    def __del__(self):
        self.conn.close()

    def execute_sql_command(self, sql_command):
        print(sql_command)
        cur = self.conn.cursor()
        cur.execute(sql_command)
        self.conn.commit()
        ret = cur.fetchall()
        cur.close()
        return ret

    def db_setup(self):
        cur = self.conn.cursor()
        if (
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name='annotations'"
            )
            != 0
        ):
            return
        else:
            cur.execute(open("schema.sql", "r").read())

    def create_project(self, project_name, contact_name, contact_email, code):
        sql_command = f"SELECT * FROM projects WHERE project_name={project_name}"
        project_exists = self.execute_sql_command(sql_command)
        if len(project_exists) > 0:
            sql_command = f"INSERT INTO projects (project_name, contact_name, contact_email, ticket_code) VALUES ('{project_name}', '{contact_name}', '{contact_email}', '{code}')"
            return self.execute_sql_command(sql_command)

    def create_annotation(self, sample_accession, attr, val):
        sql_command = f"INSERT INTO annotations (sample_accession, attr, val) VALUES ({sample_accession}, '{attr}', '{val}')"
        return self.execute_sql_command(sql_command)

    def create_annotations(self, annotations):
        sql_command = "INSERT INTO annotations (sample_accession, attr, val) VALUES "
        sql_command += ", ".join([f"({s}, '{a}', '{v}')" for s, a, v in annotations])
        return self.execute_sql_command(sql_command)

    def create_sample(
        self, sample_name, submission_id, sample_type, subject_id, host_species
    ):
        sql_command = f"INSERT INTO samples (sample_name, submission_id, sample_type, subject_id, host_species) VALUES ('{sample_name}', {submission_id}, '{sample_type}', '{subject_id}', '{host_species}')"
        self.execute_sql_command(sql_command)

        sql_command = f"SELECT sample_accession FROM samples WHERE sample_name='{sample_name}' AND submission_id='{submission_id}'"
        return self.execute_sql_command(sql_command).strip()

    def create_samples(self, samples):
        sql_command = "INSERT INTO samples (sample_name, submission_id, sample_type, subject_id, host_species) VALUES "
        sql_command += ", ".join(
            [f"('{n}', {s}, '{t}', '{i}', '{h}')" for n, s, t, i, h in samples]
        )
        self.execute_sql_command(sql_command)

        sql_command = f"SELECT sample_accession FROM samples WHERE sample_name='{samples[0][0]}' AND submission_id='{samples[0][1]}'"
        return int(self.execute_sql_command(sql_command).strip())

    def create_submission(self, project_id, comment):
        time_submitted = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        sql_command = f"INSERT INTO submissions (project_id, time_submitted, comment) VALUES ({project_id}, '{time_submitted}', '{comment}')"
        self.execute_sql_command(sql_command)

        sql_command = f"SELECT submission_id FROM submissions WHERE time_submitted='{time_submitted}'"
        return self.execute_sql_command(sql_command).strip()

    def project_hash_collision(self, code):
        sql_command = f"SELECT COUNT(*) FROM projects WHERE ticket_code='{code}'"
        result = self.execute_sql_command(sql_command)
        return int(result.strip()) > 0

    def get_project_from_project_code(self, code):
        sql_command = f"SELECT * FROM projects WHERE ticket_code='{code}'"
        res = self.execute_sql_command(sql_command)
        return res.strip().split("|")
