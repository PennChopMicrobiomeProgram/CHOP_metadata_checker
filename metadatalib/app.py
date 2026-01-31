import csv
import os
from io import StringIO
from pathlib import Path

from cachelib.file import FileSystemCache
from flask import (
    Flask,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_session import Session
from tablemusthave import Table
from werkzeug.middleware.proxy_fix import ProxyFix
from metadatalib import __version__
from metadatalib.consts import ALLOWED_EXTENSIONS
from metadatalib.spec import allowed_file, lite_specification
from metadatalib.table import run_checks, run_fixes
from metadatalib.table_flask import table_from_file

SESSION_TYPE = "cachelib"
SESSION_SERIALIZATION_FORMAT = "json"
SESSION_CACHELIB = FileSystemCache(threshold=500, cache_dir=".sessions/")


def _store_table_in_session(table: Table) -> None:
    session["table_data"] = {
        "cols": list(table.data.keys()),
        "rows": list(zip(*table.data.values())),
    }


def _table_from_session() -> Table:
    table_data = session.get("table_data", {"cols": [], "rows": []})
    return Table(table_data["cols"], table_data["rows"])


def _configure_app(app: Flask) -> None:
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(12))
    app.config["SESSION_TYPE"] = SESSION_TYPE
    app.config["SESSION_SERIALIZATION_FORMAT"] = SESSION_SERIALIZATION_FORMAT
    app.config["SESSION_CACHELIB"] = SESSION_CACHELIB
    Session(app)

    # This line is only used in production mode on a nginx server, follow instructions to setup forwarding for
    # whatever production server you are using instead. It's ok to leave this in when running the dev server.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


def _register_common_routes(app: Flask) -> None:
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

    @app.route("/health")
    def health():
        return {"status": "ready"}, 200


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("dne.html"), 404

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def internal_server_error(e):
        # Figure out best method for alert on error
        # This should probably contact someone to let them know something went wrong
        return (
            render_template(
                "dne.html",
                message="Sorry! Something went wrong on our end. We've been notified and are working to fix it.",
            ),
            500,
        )


def _register_lite_routes(app: Flask) -> None:
    @app.route("/", methods=["GET", "POST"], endpoint="index")
    def lite_index():
        message = request.args.get("message")
        filename = None

        if request.args.get("fix"):
            table = _table_from_session()
            if table.colnames():
                run_fixes(table, specification=lite_specification)
                _store_table_in_session(table)

        if request.method == "POST":
            if "metadata_upload" not in request.files:
                message = "Please select a file"
            else:
                file_fp = request.files["metadata_upload"]

                if file_fp.filename == "":
                    message = "No file selected"
                elif not allowed_file(file_fp.filename):
                    message = f"Please use the allowed file extensions for the metadata {ALLOWED_EXTENSIONS}"
                else:
                    table = table_from_file(file_fp)
                    _store_table_in_session(table)
                    filename = file_fp.filename

        table = _table_from_session()
        has_download = bool(table.colnames())
        checks = None
        if table.colnames():
            table, checks = run_checks(table, specification=lite_specification)

        return render_template(
            "lite.html",
            filename=filename,
            message=message,
            table=table if checks else None,
            checks=checks,
            has_download=has_download,
        )

    @app.route("/download", methods=["GET"], endpoint="lite_download")
    def lite_download():
        table = _table_from_session()
        if not table.colnames():
            return redirect(
                url_for("index", message="No metadata available to download yet.")
            )

        csv_file = StringIO()
        writer = csv.writer(csv_file)
        writer.writerow(table.data.keys())
        for row in zip(*table.data.values()):
            writer.writerow(row)

        response = make_response(csv_file.getvalue())
        response.headers["Content-Disposition"] = (
            "attachment; filename=metadata-session.csv"
        )
        response.headers["Content-type"] = "text/csv"
        return response


def _register_full_routes(app: Flask) -> None:
    from flask_sqlalchemy import SQLAlchemy

    from metadatalib.config import get_database_uri
    from metadatalib.models import Base, Project, Submission
    from metadatalib.utils import export_table, import_table, is_importable

    db = SQLAlchemy(model_class=Base)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    db.init_app(app)

    with app.app_context():
        db.create_all()

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
                message=(
                    f"Project {submission.project_id} with submission {submission_id} does not exist"
                ),
            )

        table = export_table(db, submission_id)
        table, checks = run_checks(table)

        return render_template(
            "submission.html",
            submission=submission,
            project=project,
            table=table,
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
                message=(
                    f"Project {submission.project_id} with submission {submission_id} does not exist"
                ),
            )

        table = export_table(db, submission_id)

        csv_file = StringIO()
        writer = csv.writer(csv_file)
        writer.writerow(table.data.keys())
        for row in zip(*table.data.values()):
            writer.writerow(row)

        # Create the response and set the appropriate headers
        response = make_response(csv_file.getvalue())
        response.headers["Content-Disposition"] = (
            f"attachment; filename={project.contact_name}-{project.project_name}_{submission.version}.csv"
        )
        response.headers["Content-type"] = "text/csv"
        return response

    @app.route("/upload/<ticket_code>", methods=["GET", "POST"])
    def upload(ticket_code):
        project = (
            db.session.query(Project).filter(Project.ticket_code == ticket_code).first()
        )
        recent_submissions = (
            db.session.query(Submission)
            .filter(Submission.project_id == project.project_id)
            .order_by(Submission.time_submitted.desc())
            .limit(3)
            .all()
        )

        if not project:
            return render_template("dne.html", ticket_code=ticket_code)
        if request.method == "GET":
            return render_template(
                "upload.html",
                project=project,
                submissions=recent_submissions,
                filename=request.args.get("filename", None),
                message=request.args.get("message", None),
            )
        if "metadata_upload" not in request.files:
            return redirect(
                url_for(
                    "upload",
                    ticket_code=project.ticket_code,
                    message="Please select a file",
                )
            )
        file_fp = request.files["metadata_upload"]

        if file_fp.filename == "":
            return redirect(
                url_for(
                    "upload",
                    ticket_code=project.ticket_code,
                    message="No file selected",
                )
            )

        if file_fp and not allowed_file(file_fp.filename):
            return redirect(
                url_for(
                    "upload",
                    ticket_code=project.ticket_code,
                    filename=file_fp.filename,
                    message=f"Please use the allowed file extensions for the metadata {ALLOWED_EXTENSIONS}",
                )
            )

        if file_fp and allowed_file(file_fp.filename):
            table = table_from_file(file_fp)
            _store_table_in_session(table)

            return redirect(url_for("submit", ticket_code=project.ticket_code))

        return redirect(url_for("upload", ticket_code=project.ticket_code))

    @app.route("/submit/<ticket_code>")
    def submit(ticket_code):
        project = (
            db.session.query(Project).filter(Project.ticket_code == ticket_code).first()
        )
        recent_submissions = (
            db.session.query(Submission)
            .filter(Submission.project_id == project.project_id)
            .order_by(Submission.time_submitted.desc())
            .limit(3)
            .all()
        )

        if not project:
            return render_template("dne.html", ticket_code=ticket_code)

        if request.args.get("fix", False, bool):
            table = _table_from_session()
            run_fixes(table)
            _store_table_in_session(table)

        table = _table_from_session()
        table, checks = run_checks(table)

        return render_template(
            "submit.html",
            project=project,
            submissions=recent_submissions,
            table=table,
            checks=checks,
            is_importable=is_importable(table),
        )

    @app.route("/review/<ticket_code>", methods=["GET", "POST"])
    def review(ticket_code):
        if request.method == "POST":
            table_data = session.pop("table_data", {"cols": [], "rows": []})
            if table_data == {"cols": [], "rows": []}:
                flash(
                    "Something went wrong! There's no metadata in the system to submit. Please try again and be sure not to reload or go back in your browser."
                )
                return redirect(url_for("submit", ticket_code=ticket_code))
            table = Table(table_data["cols"], table_data["rows"])
            import_table(table, db, ticket_code, request.form["comment"])

        return render_template("final.html", ticket_code=ticket_code)

    @app.route("/summary")
    def summary():
        return render_template(
            "summary.html",
            projects=db.session.query(Project).all(),
            submissions=db.session.query(Submission).all(),
        )

    @app.route("/", methods=["GET", "POST"], endpoint="index")
    def index():
        if request.method == "POST":
            sanitized_ticket_code = "".join(
                c for c in request.form["ticket_code"] if c.isalnum()
            )
            return redirect(
                url_for(
                    "upload",
                    ticket_code=sanitized_ticket_code,
                )
            )

        return render_template("index.html")


def create_app(mode: str | None = None) -> Flask:
    app = Flask(__name__)
    _configure_app(app)

    app_mode = (mode or os.environ.get("METADATA_APP_MODE", "full")).lower()
    app.config["APP_MODE"] = app_mode

    _register_common_routes(app)
    if app_mode == "lite":
        _register_lite_routes(app)
    else:
        _register_full_routes(app)
    _register_error_handlers(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
