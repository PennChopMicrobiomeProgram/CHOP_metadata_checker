import datetime
from typing import Optional
from tablemusthave import Table
from flask_sqlalchemy import SQLAlchemy
from metadatalib.consts import (
    CHOP_MANDATORY_TUBE,
    DEFAULT_SAMPLE_FIELDS,
)
from metadatalib.models import (
    Annotation,
    Project,
    Sample,
    Submission,
)


def get_nullable_field(t: Table, i: int, field: str) -> Optional[str]:
    try:
        return t.get(field)[i]
    except IndexError:
        return None


### NOTE ###
# These functions are here because they use the flask_sqlalchemy db client
# Everything in metadatalib uses the standard sqlalchemy client
def import_table(
    t: Table, db: SQLAlchemy, project_code: str, comment: str
) -> Submission:
    # Create submission
    project_id = (
        db.session.query(Project)
        .filter(Project.ticket_code == project_code)
        .first()
        .project_id
    )

    version = (
        db.session.query(Submission).filter(Submission.project_id == project_id).count()
        + 1
    )

    submission = Submission(
        project_id=project_id,
        version=version,
        time_submitted=datetime.datetime.now().strftime("%m-%d-%Y, %H:%M:%S"),
        comment=comment,
    )
    db.session.add(submission)
    db.session.commit()

    # Create samples
    cols = t.colnames()

    num_samples = len(t.get(cols[cols.index("SampleID")]))
    samples: list[Sample] = []
    annotations: list[Annotation] = []

    for i in range(num_samples):
        samples.append(
            Sample(
                sample_name=t.get("SampleID")[i],
                submission_id=submission.submission_id,
                sample_type=get_nullable_field(t, i, "sample_type"),
                subject_id=get_nullable_field(t, i, "subject_id"),
                host_species=get_nullable_field(t, i, "host_species"),
            )
        )

    db.session.add_all(samples)
    db.session.commit()

    # Create annotations after samples are commited to get sample_accession
    # If accessed before commit, sample_accession will be None
    for i in range(num_samples):
        for j, col_name in enumerate(cols):
            # Create annotations
            if col_name not in DEFAULT_SAMPLE_FIELDS:
                if t.get(cols[j])[i] is not None:
                    annotations.append(
                        Annotation(
                            sample_accession=samples[i].sample_accession,
                            attr=cols[j],
                            val=t.get(cols[j])[i],
                        )
                    )

    db.session.add_all(annotations)
    db.session.commit()

    return submission


def is_importable(t: Table) -> bool:
    return all(col in t.colnames() for col in CHOP_MANDATORY_TUBE)


def export_table(db: SQLAlchemy, submission_id: int) -> Table:
    samples = (
        db.session.query(Sample).filter(Sample.submission_id == submission_id).all()
    )

    annotations = (
        db.session.query(Annotation)
        .filter(
            Annotation.sample_accession.in_(
                [sample.sample_accession for sample in samples]
            )
        )
        .all()
    )

    cols = DEFAULT_SAMPLE_FIELDS.copy()
    for annotation in annotations:
        if annotation.attr not in cols:
            cols.append(annotation.attr)

    rows = []
    for sample in samples:
        row = [
            sample.sample_name,
            sample.sample_type,
            sample.subject_id,
            sample.host_species,
        ]

        for col in [c for c in cols if c not in DEFAULT_SAMPLE_FIELDS]:
            row.append(
                next(
                    (
                        a.val
                        for a in annotations
                        if a.attr == col
                        and a.sample_accession == sample.sample_accession
                    ),
                    None,
                )
            )
        rows.append(row)

    return Table(cols, rows)
