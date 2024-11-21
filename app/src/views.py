from flask_sqlalchemy import SQLAlchemy
from app.metadatalib.src.metadatalib import Annotation, Project, Sample, Submission


class ShowProject:
    def __init__(self, db: SQLAlchemy, ticket_code: str):
        self.ticket_code = ticket_code
        self.db = db
        self.project = (
            self.db.session.query(Project)
            .filter(Project.ticket_code == self.ticket_code)
            .first()
        )
        self.submissions = (
            self.db.session.query(Submission)
            .filter(Submission.project_id == self.project.project_id)
            .all()
        )


class ShowSubmission:
    def __init__(self, db: SQLAlchemy, submission_id: int):
        self.submission_id = submission_id
        self.db = db
        self.submission = (
            self.db.session.query(Submission)
            .filter(Submission.submission_id == self.submission_id)
            .first()
        )
        if self.submission:
            self.project = (
                self.db.session.query(Project)
                .filter(Project.project_id == self.submission.project_id)
                .first()
            )
        else:
            self.project = None


class Download(ShowSubmission):
    def __init__(self, db: SQLAlchemy, submission_id: int):
        super().__init__(db, submission_id)


class Submit:
    def __init__(self, db: SQLAlchemy, ticket_code: str):
        self.ticket_code = ticket_code
        self.db = db
        self.project = (
            self.db.session.query(Project)
            .filter(Project.ticket_code == self.ticket_code)
            .first()
        )
        self.submissions = (
            self.db.session.query(Submission)
            .filter(Submission.project_id == self.project.project_id)
            .order_by(Submission.time_submitted.desc())
            .limit(3)
            .all()
        )
