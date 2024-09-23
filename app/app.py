import csv
import os
from app.src.utils import export_table, import_table, run_checks, table_from_file
from app.metadatalib.src.metadatalib import SQLALCHEMY_DATABASE_URI
from app.metadatalib.src.metadatalib.models import (
    Annotation,
    Base,
    Project,
    Sample,
    Submission,
)
from app.metadatalib.src.metadatalib.utils import allowed_file
from flask import (
    Flask,
    make_response,
    render_template,
    url_for,
    request,
    redirect,
    flash,
    send_from_directory,
    session,
)
from flask_sqlalchemy import SQLAlchemy
from io import StringIO
from pathlib import Path
from tablemusthave import Table
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.datastructures import FileStorage

app = Flask(__name__)
app.secret_key = os.urandom(12)

# This line is only used in production mode on a nginx server, follow instructions to setup forwarding for
# whatever production server you are using instead. It's ok to leave this in when running the dev server.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
print(SQLALCHEMY_DATABASE_URI)
db = SQLAlchemy(model_class=Base)
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        Path(app.root_path) / "static",
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/wiki")
def wiki():
    app.logger.info("Rendering wiki.html.\n")
    return render_template("wiki.html")


@app.route("/project/<ticket_code>")
def show_project(ticket_code):
    project = (
        db.session.query(Project).filter(Project.ticket_code == ticket_code).first()
    )
    submissions = (
        db.session.query(Submission)
        .filter(Submission.project_id == project.project_id)
        .all()
    )

    if not project:
        return render_template("dne.html", ticket_code=ticket_code)

    return render_template("project.html", project=project, submissions=submissions)


@app.route("/submission/<submission_id>")
def show_submission(submission_id):
    submission = (
        db.session.query(Submission)
        .filter(Submission.submission_id == submission_id)
        .first()
    )

    if not submission:
        return render_template("dne.html", submission_id=submission_id)

    project = (
        db.session.query(Project)
        .filter(Project.project_id == submission.project_id)
        .first()
    )

    if not project:
        return render_template(
            "dne.html",
            project_id=submission.project_id,
            message=f"Project {submission.project_id} with submission {submission_id} does not exist",
        )

    t = export_table(db, submission_id)
    t, checks = run_checks(t=t)

    return render_template(
        "submission.html",
        submission=submission,
        project=project,
        table=t,
        checks=checks,
    )


@app.route("/download/<submission_id>", methods=["GET", "POST"])
def download(submission_id):
    submission = (
        db.session.query(Submission)
        .filter(Submission.submission_id == submission_id)
        .first()
    )

    if not submission:
        return render_template("dne.html", submission_id=submission_id)

    project = (
        db.session.query(Project)
        .filter(Project.project_id == submission.project_id)
        .first()
    )

    if not project:
        return render_template(
            "dne.html",
            project_id=submission.project_id,
            message=f"Project {submission.project_id} with submission {submission_id} does not exist",
        )

    t = export_table(db, submission_id)

    csv_file = StringIO()
    writer = csv.writer(csv_file)
    writer.writerow(t.data.keys())
    for row in zip(*t.data.values()):
        writer.writerow(row)

    # Create the response and set the appropriate headers
    response = make_response(csv_file.getvalue())
    response.headers["Content-Disposition"] = (
        f"attachment; filename={project.contact_name}-{project.project_name}_{submission.version}.csv"
    )
    response.headers["Content-type"] = "text/csv"
    return response


@app.route("/review/<ticket_code>", methods=["GET", "POST"])
def review(ticket_code):
    if request.method == "POST":
        table_data = session.pop("table_data", {"cols": [], "rows": []})
        t = Table(table_data["cols"], table_data["rows"])
        import_table(t, db, ticket_code, request.form["comment"])

    return render_template("final.html", ticket_code=ticket_code)


@app.route("/submit/<ticket_code>", methods=["GET", "POST"])
def submit(ticket_code):
    project = (
        db.session.query(Project).filter(Project.ticket_code == ticket_code).first()
    )

    if not project:
        return render_template("dne.html", ticket_code=ticket_code)
    elif request.method == "GET":
        # Display submission page for ticket_code
        return render_template(
            "submit.html",
            filename="Select file ...",
            project=project,
        )
    elif request.method == "POST":
        # Check if post request has a file
        if "metadata_upload" not in request.files:
            flash("Please select a file")
            return redirect(url_for("submit", ticket_code=project.ticket_code))
        file_fp = request.files["metadata_upload"]

        # Check if user submitted a file
        if file_fp.filename == "":
            flash("No file selected")
            return redirect(url_for("submit", ticket_code=project.ticket_code))

        # Check if file was submitted and if it has correct extensions
        if file_fp and not allowed_file(file_fp.filename):
            flash(
                "Please use the allowed file extensions for the metadata {.tsv, .csv}"
            )
            return redirect(url_for("submit", ticket_code=project.ticket_code))

        if file_fp and allowed_file(file_fp.filename):
            t, checks = run_checks(table_from_file(file_fp))
            print(t.data.keys())
            print(list(zip(*t.data.values())))
            session["table_data"] = {
                "cols": list(t.data.keys()),
                "rows": list(zip(*t.data.values())),
            }

            return render_template(
                "submit.html",
                filename=file_fp.filename,
                project=project,
                table=t,
                checks=checks,
            )

        return redirect(url_for("submit", ticket_code=project.ticket_code))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sanitized_ticket_code = "".join(
            c for c in request.form["ticket_code"] if c.isalnum()
        )
        return redirect(
            url_for(
                "submit",
                ticket_code=sanitized_ticket_code,
            )
        )

    return render_template("index.html", projects=db.session.query(Project).all())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
