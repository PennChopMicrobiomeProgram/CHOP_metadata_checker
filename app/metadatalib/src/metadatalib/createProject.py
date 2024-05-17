# Functions for creating new project in DB and returning a metadata checker site URL
import random

from .db import MetadataDB


# Creates new project in DB and returns URL
# @param db is the database to interact with (sqlite)
# @param proj is the name of the project
# @param customer is the customer name for the project
# @param email is the contact email for the project
# @return is the unique project code
def createProject(db: MetadataDB, proj: str, customer: str, email: str) -> str:
    code = "%030x" % random.randrange(16**30)
    while db.project_hash_collision(code):
        code = "%030x" % random.randrange(16**30)

    db.create_project(proj, customer, email, code)

    return code
