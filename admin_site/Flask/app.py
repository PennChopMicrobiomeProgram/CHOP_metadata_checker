import os
import random

from flask import Flask, render_template, url_for, request, redirect, flash, session, send_from_directory
from pathlib import Path
from db.db import MetadataDB
from dotenv import load_dotenv
load_dotenv(Path.cwd() / '../../CHOP.env')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
db_fp = os.environ.get('DB_FP')

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/', methods=['GET', 'POST'])
def index():
    code = ""
    if request.method == 'POST':
        db = MetadataDB(db_fp)
        code = '%030x' % random.randrange(16**30)
        while db.project_hash_collision(code):
            code = '%030x' % random.randrange(16**30)
        
        db.create_project(request.form['project_name'], request.form['contact_name'], request.form['contact_email'], code)

    return render_template('index.html', code=code)