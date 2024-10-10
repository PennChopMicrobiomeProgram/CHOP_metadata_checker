import datetime
import io
from flask import flash
from tablemusthave import Table, musthave
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_sqlalchemy import SQLAlchemy
from tablemusthave import Table
from app.metadatalib.src.metadatalib.consts import (
    DEFAULT_SAMPLE_FIELDS,
    REGEX_TRANSLATE,
)
from app.metadatalib.src.metadatalib.models import (
    Annotation,
    Project,
    Sample,
    Submission,
)
from app.metadatalib.src.metadatalib.utils import (
    no_leading_trailing_whitespace,
    specification,
)


def get_nullable_field(t: Table, i: int, field: str) -> str:
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


def table_from_file(file_fp: FileStorage) -> Table:
    filename = secure_filename(file_fp.filename)
    delim = ","

    # Convert FileStorage to StringIO to read as csv/tsv object
    string_io = io.StringIO(file_fp.read().decode("utf-8-sig"), newline=None)
    if filename.rsplit(".", 1)[1].lower() in ["tsv", "txt"]:
        delim = "\t"

    return Table.from_csv(string_io, delimiter=delim)


def run_checks(t: Table) -> tuple[Table, dict]:
    # Get metadata table to print on webpage
    headers = t.colnames()
    sample_num = len(t.get(t.colnames()[0]))
    rows = list(range(0, sample_num))

    for h in headers:
        specification.append(no_leading_trailing_whitespace(h))

    # Overall check to see if metadata satisfies all requirements
    checks = specification.check(t)
    all_msg = [msg[1].message() for msg in checks]
    checks_passed = False
    if all(msg == "OK" or "Doesn't apply" in msg for msg in all_msg):
        flash("Your metadata is good to go!")
        checks_passed = True
    else:
        flash("Your metadata still has errors!")
        checks_passed = False

    # Create dictionaries for misformmated cell highlighting and popover text
    header_issues = {}
    highlight_missing = {}
    highlight_mismatch = {}
    highlight_repeating = {}
    highlight_not_allowed = {}

    ##print requirements and save the errors in the dictionarys to highlight in table
    for req, res in specification.check(t):
        if isinstance(res, musthave.StillNeeds):
            ##print(req.__dict__)
            ##print(res.__dict__)
            ##populate missing dictionary with empty cells
            if res.idxs is not None:
                for row_num in res.idxs:
                    for col_nam in req.colnames:
                        if row_num in highlight_missing.keys():
                            highlight_missing = {
                                **highlight_missing,
                                **{row_num: highlight_missing[row_num] + [col_nam]},
                            }
                        else:
                            highlight_missing = {
                                **highlight_missing,
                                **{row_num: [col_nam]},
                            }
                ##populate header dictionary for empty cell dictionary
                if len(req.colnames) == 1:
                    header_issues = {**header_issues, **{req.colnames[0]: "Empty cell"}}
                ##populate header dictionary for unique cells between 2 or more columns
                else:
                    header_issues = {
                        **header_issues,
                        **{
                            req.colnames[0]: (
                                " + ".join(req.colnames) + " must be filled in together"
                            )
                        },
                    }
            ##populate mismatch dictionary for illegally formmated cells (e.g. containing specials characters)
            if res.not_matching is not None and hasattr(req, "colname"):
                highlight_mismatch = {
                    **highlight_mismatch,
                    **{cells: req.colname for cells in res.not_matching},
                }
                header_issues = {**header_issues, **{req.colname: "Wrong formatting"}}
            ##populate header dictionary with column names with wrong format
            if res.not_matching is not None and not hasattr(req, "colname"):
                header_issues = {
                    **header_issues,
                    **{
                        col_names: "Forbidden characters in column name"
                        for col_names in res.not_matching
                    },
                }
            ##populate repeating dictionary with repeating cells
            if res.repeated is not None:
                highlight_repeating = {
                    **highlight_repeating,
                    **{cells[0][0]: req.colnames[0] for cells in res.repeated},
                }
                header_issues = {
                    **header_issues,
                    **{req.colnames[0]: "Repeated values"},
                }
            ##populate dictionary with cells that does not hold a pre-selected option
            if res.not_allowed is not None:
                highlight_not_allowed = {
                    **highlight_not_allowed,
                    **{cells: req.colname for cells in res.not_allowed},
                }
                header_issues = {
                    **header_issues,
                    **{req.colname: "Use only allowed selections"},
                }
        ##print error messages
        if res.message() != "OK" and "Doesn't apply" not in res.message():
            modified_descrip = req.description()[:-1]
            for keys in REGEX_TRANSLATE.keys():
                if keys in req.description():
                    modified_descrip = (
                        modified_descrip.split("match")[0] + REGEX_TRANSLATE[keys]
                    )
            flash(modified_descrip + ": " + res.message())

    return (
        t,
        {
            "headers": headers,
            "rows": rows,
            "missing": highlight_missing,
            "mismatch": highlight_mismatch,
            "repeating": highlight_repeating,
            "not_allowed": highlight_not_allowed,
            "header_issues": header_issues,
            "passed": checks_passed,
        },
    )
