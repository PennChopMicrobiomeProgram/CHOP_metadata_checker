# CHOP Metadata Checker

## Introduction

This is a Flask application for checking metadata sheets for the PennCHOP Microbiome Core.

An older version is hosted at ctbus.pythonanywhere.com.

## Installation and Running

To run the flask app on its own (i.e. in development mode) follow the instructions in Running Flask App. To run it in production mode follow Production Mode on Nginx after setting it up in dev mode.

### Running Flask App

Clone the repo and start by making a copy of `SAMPLE.env` called CHOP.env, filling in any blank values (SECRET_KEY can be any string), and use sqlite to initialize the database based on schema.sql (you can call it anything you want, DB.db is used below). Next install the required python packages listed in `requirements.txt`. Then start the flask app.

```
git clone git@github.com:PennChopMicrobiomeProgram/CHOP_metadata_checker.git
cd CHOP_metadata_checker
cp SAMPLE.env CHOP.env
**Make changes to CHOP.env in editor of your choice**
sqlite3 DB.db < schema.sql
pip install -r requirements.txt
flask --app=app/app run -p 5000 >> logs/log.app 2>&1
```
### Production Mode on Nginx

Follow the [nginx docs](https://docs.nginx.com/) to set up a server. Then follow [this guide](https://flask.palletsprojects.com/en/2.2.x/deploying/nginx/) from flask to set up forwarding from nginx to flask. Use something like the script below to start flask automatically on server restarts.

```
#!/bin/bash

CONDA_BASE=$(conda info --base)
source $CONDA_BASE/etc/profile.d/conda.sh
conda activate metadata_checker

cd /path/to/CHOP_metadata_checker/
sudo nohup flask --app=app/app run -p 5000 >> logs/log.app 2>&1
echo "Metadata checker started!"
```

## Using the metadatacli to Create Projects

Use the metadatacli to create new projects in the database.

```
pip install -e metadatacli/
metadatacli PROJECT_NAME CLIENT_NAME CLIENT_EMAIL
```
