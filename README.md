# CHOP Metadata Checker

## Introduction

This is a Flask application for checking metadata sheets for the PennCHOP Microbiome Core. It uses a PostgreSQL database hosted on reslncmcadmin01.research.chop.edu and is deployed through TKG Kubernetes.

An older version is hosted at ctbus.pythonanywhere.com (consider this deprecated, i.e. not guaranteed to exist at any point in the future).

## Installation and Running

To run the flask app on its own (i.e. in development mode) follow the instructions in Running Flask App for Debugging. To run it in production mode follow Production Mode on K8s. For installing the metadatalib CLI, go to Using the metadatacli for Creating Projects.

### Running Flask App for Debugging

Clone the repo and start by making a copy of `SAMPLE.env` called CHOP.env, filling in any blank values (SECRET_KEY can be any string), and use sqlite to initialize the database based on schema.sql (you can call it anything you want, DB.db is used below). Next install the required python packages listed in `requirements.txt`. Then start the flask app.

```
git clone git@github.com:PennChopMicrobiomeProgram/CHOP_metadata_checker.git
cd CHOP_metadata_checker
cp SAMPLE.env CHOP.env
**Make changes to CHOP.env in editor of your choice**
sqlite3 DB.db < schema.sql
pip install -r requirements.txt
export FLASK_DEBUG=1 && flask --app=app/app run -p 5000
```
### Production Mode on K8s

Add Postgres password as a Secret:

```
kubectl create secret generic pg-password --from-literal=DB_PSWD=<enter_db_password_here>
```

This secret is mounted in `deployment.yaml`. To check the status of the cluster, login with `kubectl` and run `kubectl get all`. To check the logs of a specific pod use:

```
kubectl logs --since=48h podname
```

To jump into a shell in a pod use:

```
kubectl exec -it podname -- /bin/bash
```

## Using the metadatacli to Create Projects

Use the metadatacli to create new projects in the database. First you'll need to be on the right machine. This can mean either SSHing into reslncmcadmin01 and `cd`ing to the CHOP_metadata_checker/ directory or using `kubectl exec -it <podname> -- /bin/bash` to jump into a K8s pod. On the server there should already be a .env file with all the necessary environment setup and in the pod the environment should be preset by the container and/or deployment; so no need to worry about env setup. Just install the lib and run the metadatacli command to create a new project:

```
pip install -r requirements.txt
pip install app/metadatalib/
metadatacli -p PROJECT_NAME -n CLIENT_NAME -e CLIENT_EMAIL
```
