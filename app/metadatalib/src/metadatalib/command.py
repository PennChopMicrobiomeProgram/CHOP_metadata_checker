import argparse
import os
import random
import sys
from datetime import datetime

from sqlalchemy import insert, select

from metadatalib.models import Project
from metadatalib import __version__, session


def _create_project(args):
    code = "%030x" % random.randrange(16**30)
    while session.scalar(select(Project).filter(Project.ticket_code == code)):
        code = "%030x" % random.randrange(16**30)

    session.scalar(
        insert(Project)
        .returning(Project.ticket_code)
        .values(
            {
                "project_name": " ".join(args.project_name),
                "contact_name": " ".join(args.customer_name),
                "contact_email": " ".join(args.customer_email),
                "ticket_code": code,
            }
        )
    )

    url = os.environ.get("URL", "") + "/submit/" + code
    print(url)
    return code


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument(
        "-p", "--project_name", nargs="+", default=[], help="Name of the project"
    )
    p.add_argument(
        "-n", "--customer_name", nargs="+", default=[], help="Name of the customer"
    )
    p.add_argument(
        "-e",
        "--customer_email",
        nargs="+",
        default=[],
        help="Contact email for the customer",
    )
    p.add_argument("-v", "--version", action="version", version=__version__)

    args = p.parse_args(argv)

    if args.project_name == [] or args.customer_name == [] or args.customer_email == []:
        print(
            "ERR: Please provide arguments for each option (--project_name, --customer_name, and --customer_email)."
        )
        sys.exit(0)

    code = _create_project(args)
    print(
        f"{datetime.now()}\nProject code: {code}\nProject name: {args.project_name}\nClient name: {args.customer_name}\n"
    )
