import os
from flask import (
    Flask,
    render_template,
    url_for,
    request,
    redirect,
    flash,
    send_from_directory,
)
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from metadatalib import SQLALCHEMY_DATABASE_URI
from metadatalib.models import Base, Project
from metadatalib.utils import allowed_file
from metadatalib.pages import post_review, run_checks
from tablemusthave import Table
from werkzeug.middleware.proxy_fix import ProxyFix

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

t = Table([], [])


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


@app.route("/review/<ticket_code>", methods=["GET", "POST"])
def review(ticket_code):
    if request.method == "POST":
        submission = post_review(t, db, ticket_code, request.form["comment"])

    return render_template("final.html", ticket_code=ticket_code)


@app.route("/submit/<ticket_code>", methods=["GET", "POST"])
def submit(ticket_code):
    filename = "Select file ..."
    project = (
        db.session.query(Project).filter(Project.ticket_code == ticket_code).first()
    )

    if not project:
        # Check that ticket_code exists in the database
        return render_template("dne.html", project=project)
    elif request.method == "GET":
        # Display submission page for ticket_code
        return render_template(
            "submit.html",
            filename=filename,
            project=project,
        )
    elif request.method == "POST":
        # Check if post request has a file
        if "metadata_upload" not in request.files:
            flash("Please select a file")
            return redirect(url_for("submit", project=project))
        file_fp = request.files["metadata_upload"]

        # Check if user submitted a file
        if file_fp.filename == "":
            flash("No file selected")
            return redirect(url_for("submit", project=project))

        # Check if file was submitted and if it has correct extensions
        if file_fp and not allowed_file(file_fp.filename):
            flash(
                "Please use the allowed file extensions for the metadata {.tsv, .csv}"
            )
            return redirect(url_for("submit", project=project))

        if file_fp and allowed_file(file_fp.filename):
            global t
            (
                t,
                headers,
                rows,
                highlight_missing,
                highlight_mismatch,
                highlight_repeating,
                highlight_not_allowed,
                header_issues,
                checks_passed,
            ) = run_checks(file_fp)

            return render_template(
                "submit.html",
                filename=filename,
                project=project,
                headers=headers,
                rows=rows,
                table=t,
                missing=highlight_missing,
                mismatch=highlight_mismatch,
                repeating=highlight_repeating,
                not_allowed=highlight_not_allowed,
                header_issues=header_issues,
                checks_passed=checks_passed,
            )

        return redirect(url_for("submit", project=project))


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

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
