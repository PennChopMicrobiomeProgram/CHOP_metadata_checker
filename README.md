# CHOP Metadata Checker

## Introduction

This is a Flask application for checking metadata sheets for the PennCHOP Microbiome Core.

Hosted at https://tuv292.pythonanywhere.com

## Installation and Running

Clone the repo and start by making a copy of `SAMPLE.env` called CHOP.env, filling in any blank values (SECRET_KEY can be any string). Next install the metadata cli by navigating into the directory and installing with `pip`. Then return to the root directory and use sqlite to initialize the database based on schema.sql (you can call it anything you want, TEST.db is used below) and install requirements for the Flask app with requirements.txt. To create a new project, run metadatacli, passing in the project descriptors. To start up the website, navigate to the Flask directory and execute `flask run`.

```
git clone git@github.com:PennChopMicrobiomeProgram/CHOP_metadata_checker.git
cd CHOP_metadata_checker
cp SAMPLE.env CHOP.env
**Make changes to CHOP.env in editor of your choice**
cd metadatacli
pip install .
cd ..
sqlite3 TEST.db < schema.sql
pip install -r requirements.txt
metadatacli project_name customer_name customer_email
cd Flask
flask run
```
