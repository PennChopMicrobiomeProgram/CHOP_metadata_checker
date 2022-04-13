# CHOP Metadata Checker

## Introduction

This is a Flask application for checking metadata sheets for the PennCHOP Microbiome Core.

Hosted at https://tuv292.pythonanywhere.com

## Installation and Running

Clone the repo and start by making a copy of `SAMPLE.env` called CHOP.env, filling in any blank values (SECRET_KEY can be any string), and use sqlite to initialize the database based on schema.sql (you can call it anything you want, TEST.db is used below). Next install the metadata cli by navigating into the directory and installing with `pip`. To create a new project, run metadatacli, passing in the project descriptors. Then return to the root directory and install requirements for the Flask app with requirements.txt.  To start up the website, navigate to the Flask directory and execute `flask run`.

```
git clone git@github.com:PennChopMicrobiomeProgram/CHOP_metadata_checker.git
cd CHOP_metadata_checker
cp SAMPLE.env CHOP.env
**Make changes to CHOP.env in editor of your choice**
sqlite3 TEST.db < schema.sql
cd metadatacli
pip install .
metadatacli project_name customer_name customer_email
cd ..
pip install -r requirements.txt
cd Flask
flask run
```
