# Functions for creating new project in DB and returning a metadata checker site URL
import random

from .db import MetadataDB

# Creates new project in DB and returns URL
def createProject(db: MetadataDB, proj: str, customer: str, email: str) -> str:
    code = '%030x' % random.randrange(16**30)
    while db.project_hash_collision(code):
        code = '%030x' % random.randrange(16**30)
    
    db.create_project(proj, customer, email, code)

    return code
