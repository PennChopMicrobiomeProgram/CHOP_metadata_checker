import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SRC_ROOT, '../../../CHOP.env'))

from .createProject import createProject
from .db import MetadataDB

def _create_project(args, db):
    code = createProject(db, args.project_name, args.customer_name, args.customer_email)
    url = os.environ.get('URL') + "/submit/" + code
    print(url)
    return code

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("project_name", help="Name of the project")
    p.add_argument("customer_name", help="Name of the customer")
    p.add_argument("customer_email", help="Contact email for the customer")

    args = p.parse_args(argv)

    log_fp = os.path.join(os.environ.get('LOG_FP'), "log.cli")
    print("Writing logs to: " + log_fp)
    
    db = MetadataDB(os.environ.get('DB_FP'))

    with open(log_fp, "a+") as f:
        f.write("Creating project...\n")
    code = _create_project(args, db)
    with open(log_fp, "a+") as f:
        f.write(f"Project code: {code}\n")
    