from flask import Flask, render_template, url_for, request, redirect, flash, send_from_directory
import os
from tablemusthave import *
from metadatalib.src.db import MetadataDB
from metadatalib.src.log import Logger
from metadatalib.src.utils import allowed_file
from metadatalib.src.pages import post_review, run_checks
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv(os.path.join(app.root_path, '../CHOP.env'))
app.secret_key = os.environ.get('SECRET_KEY')

# This line is only used in production mode on a nginx server, follow instructions to setup forwarding for
# whatever production server you are using instead. It's ok to leave this in when running the dev server.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

db_fp = os.environ.get('DB_FP')
t = Table([], [])
l = Logger(os.path.join(os.environ.get('LOG_FP'), 'log.out'), os.path.join(os.environ.get('LOG_FP'), 'log.err'))

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
                              
@app.route('/wiki')
def wiki():
  l.log("Rendering wiki.html.\n")
  return render_template('wiki.html')

@app.route('/review/<project_code>', methods=['GET', 'POST'])
def review(project_code):
  if request.method == 'POST':
    db = MetadataDB(db_fp)
    post_review(t, db, project_code, request.form['comment'], l)
  l.log(f"Rendering final.html with project_code {project_code}.\n")
  return render_template('final.html', project_code=project_code)

@app.route('/submit/<project_code>', methods=['GET', 'POST'])
def submit(project_code):
  filename = "Select file ..."
  # Ideally we would have one db object for the whole app, seems like routes spawn their own threads though,
  # which sqlite doesn't play nice with
  db = MetadataDB(db_fp)

  if not db.project_hash_collision(project_code):
    l.err(f"Rendering dne.html with project_code {project_code}.\n")
    return render_template('dne.html', project_code=project_code)
  elif request.method == 'GET':
    l.log(f"Rendering submit.html with project_code {project_code} and attachment named {filename}.\n")
    project_name, client_name, client_email = [db.get_project_from_project_code(project_code)[x] for x in [1,2,3]]
    return render_template('submit.html', filename=filename, project_code=project_code, project_name=project_name, client_name=client_name, client_email=client_email)
  elif request.method == 'POST':
    # Check if post request has a file
    if 'metadata_upload' not in request.files:
      flash('Please select a file')
      l.log(f"Redirecting to submit route for no attachement with project_code {project_code}.\n")
      return redirect(url_for('submit', project_code=project_code))
    file_fp = request.files['metadata_upload']
    # Check if user submitted a file
    if file_fp.filename == '':
      flash('No file selected')
      l.err(f"Redirecting to submit route for no attachement with project_code {project_code}.\n")
      return redirect(url_for('submit', project_code=project_code))
    # Check if file was submitted and if it has correct extensions
    if file_fp and not allowed_file(file_fp.filename):
      flash('Please use the allowed file extensions for the metadata {.tsv, .csv}')
      l.err(f"Redirecting to submit route for wrong extension with project_code {project_code}.\n")
      return redirect(url_for('submit', project_code=project_code))
    
    if file_fp and allowed_file(file_fp.filename):
      global t
      t, headers, rows, highlight_missing, highlight_mismatch, highlight_repeating, highlight_not_allowed, header_issues, checks_passed = run_checks(file_fp)
      project_name, client_name, client_email = [db.get_project_from_project_code(project_code)[x] for x in [1,2,3]]
      
      l.log(f"Rendering submit.html with project_code {project_code} and attachment named {filename}. Includes\n\theaders: {headers}\n\trows: {rows}\n\ttable: {t}\n\tmissing: {highlight_missing}\n\tmismatch: {highlight_mismatch}\n\trepeating: {highlight_repeating}\n\tnot_allowed: {highlight_not_allowed}\n\theader_issues: {header_issues}\n\tchecks_passed: {checks_passed}\n")
      return render_template('submit.html', filename=filename, project_code=project_code, project_name=project_name, client_name=client_name, client_email=client_email, headers=headers, rows=rows, table=t, missing=highlight_missing, mismatch=highlight_mismatch, repeating=highlight_repeating, not_allowed=highlight_not_allowed, header_issues=header_issues, checks_passed=checks_passed)
    
    l.log(f"Redirecting to submit route with project_code {project_code}.\n")
    return redirect(url_for('submit', project_code=project_code))

@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'POST':
    l.log(f"Redirecting to submit route with project_code {request.form['project_code']}.\n")
    return redirect(url_for('submit', project_code=''.join(c for c in request.form['project_code'] if c.isalnum())))
  l.log(f"Rendering index.html.\n")
  return render_template('index.html')

if __name__ == "__main__":
  app.run(host="0.0.0.0", port="5000", debug=True)
