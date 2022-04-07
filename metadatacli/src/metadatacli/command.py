import argparse
import os
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
load_dotenv(Path.cwd() / '..' / 'CHOP.env')

from .createProject import createProject
from .db import MetadataDB

def _create_project(args, db):
    code = createProject(db, args.project_name, args.customer_name, args.customer_email)
    url = "http://127.0.0.1:5000/" + code
    print(url)
    return code

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("project_name", help="Name of the project")
    p.add_argument("customer_name", help="Name of the customer")
    p.add_argument("customer_email", help="Contact email for the customer")

    args = p.parse_args(argv)

    None if os.path.isdir("logs/") else os.mkdir("logs")
    logF = open("logs/main.log", "w")
    print("Writing logs to: " + logF.name)

    db = MetadataDB(os.environ.get('DB_FP'))

    logF.write("Creating project...")
    code = _create_project(args, db)
    logF.write("Project code: " + code)
    