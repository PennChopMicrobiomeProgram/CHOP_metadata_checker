# CHOP Metadata Checker

## Introduction

This is a Flask application for checking metadata sheets for the PennCHOP Microbiome Core.

Hosted at https://tuv292.pythonanywhere.com

## Installation and Running

Clone the repo and start by making a copy of `SAMPLE.env` called CHOP.env, filling in any blank values (SECRET_KEY can be any string), and use sqlite to initialize the database based on schema.sql (you can call it anything you want, TEST.db is used below). Next install the required python packages listed in `requirements.txt`. We can now start the two Flask sites by navigating into their respective directories and starting them running on different ports (be sure to `export FLASK_APP=app` first) with `flask run -p port_num`.

```
git clone git@github.com:PennChopMicrobiomeProgram/CHOP_metadata_checker.git
cd CHOP_metadata_checker
cp SAMPLE.env CHOP.env
**Make changes to CHOP.env in editor of your choice**
sqlite3 TEST.db < schema.sql
pip install -r requirements.txt
cd admin_site/Flask
export FLASK_APP=app
flask run -p 5000
**Use site to create new project**
**In a new terminal (or set flask to run in the background)**
cd CHOP_metadata_checker/metadata_checker_site/Flask
export FLASK_APP=app **If in new terminal session**
flask run -p 5001
**Client uses site to upload metadata**
```
