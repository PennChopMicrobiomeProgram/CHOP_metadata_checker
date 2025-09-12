from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(nullable=False, unique=True)
    contact_name: Mapped[str] = mapped_column(nullable=False)
    contact_email: Mapped[str] = mapped_column(nullable=False)
    ticket_code: Mapped[str] = mapped_column(nullable=False, unique=True)

    def __repr__(self):
        return f"<Project(project_id={self.project_id}, project_name={self.project_name}, contact_name={self.contact_name}, contact_email={self.contact_email}, ticket_code={self.ticket_code})>"


class Submission(Base):
    __tablename__ = "submissions"

    submission_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    version: Mapped[int]
    time_submitted: Mapped[str] = mapped_column(nullable=False)
    comment: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self):
        return f"<Submission(submission_id={self.submission_id}, project_id={self.project_id}, version={self.version}, time_submitted={self.time_submitted}, comment={self.comment})>"


class Sample(Base):
    __tablename__ = "samples"

    sample_accession: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sample_name: Mapped[str] = mapped_column(nullable=False)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.submission_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    sample_type: Mapped[Optional[str]] = mapped_column(default=None)
    subject_id: Mapped[Optional[str]] = mapped_column(default=None)
    host_species: Mapped[Optional[str]] = mapped_column(default=None)

    def __repr__(self):
        return f"<Sample(sample_accession={self.sample_accession}, sample_name={self.sample_name}, submission_id={self.submission_id}, sample_type={self.sample_type}, subject_id={self.subject_id}, host_species={self.host_species})>"


class Annotation(Base):
    __tablename__ = "annotations"

    sample_accession: Mapped[int] = mapped_column(
        ForeignKey("samples.sample_accession", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    attr: Mapped[str] = mapped_column(nullable=False, primary_key=True)
    val: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self):
        return f"<Annotation(sample_accession={self.sample_accession}, attr={self.attr}, val={self.val})>"
