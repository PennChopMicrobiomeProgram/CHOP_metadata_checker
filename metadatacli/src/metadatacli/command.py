import argparse
import os
import sys

from dotenv import load_dotenv
SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SRC_ROOT, '../../../CHOP.env'))

from .createProject import createProject
from .db import MetadataDB

def _create_project(args, db):
    code = createProject(db, ' '.join(args.project_name), ' '.join(args.customer_name), ' '.join(args.customer_email))
    url = os.environ.get('URL') + "/submit/" + code
    print(url)
    return code

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--project_name", nargs='+', default=[], help="Name of the project")
    p.add_argument("-n", "--customer_name", nargs='+', default=[], help="Name of the customer")
    p.add_argument("-e", "--customer_email", nargs='+', default=[], help="Contact email for the customer")

    args = p.parse_args(argv)

    if args.project_name == [] or args.customer_name == [] or args.customer_email == []:
        print("Please provide arguments for each option (--project_name, --customer_name, and --customer_email).")
        sys.exit(0)

    log_fp = os.path.join(os.environ.get('LOG_FP'), "log.cli")
    try:
        os.makedirs(os.environ.get('LOG_FP'))
    except FileExistsError as e:
        None
    print("Writing logs to: " + log_fp)
    
    db = MetadataDB(os.environ.get('DB_FP'))

    with open(log_fp, "a+") as f:
        f.write("Creating project...\n")
    code = _create_project(args, db)
    with open(log_fp, "a+") as f:
        f.write(f"Project code: {code}\n")
    
