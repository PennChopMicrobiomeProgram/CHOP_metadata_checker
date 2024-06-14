# MetadataChecker

A Flask site for validating metadata sheets per the standards of the PCMP and an associated library for project management.

[![Tests](https://github.com/PennChopMicrobiomeProgram/CHOP_metadata_checker/actions/workflows/pr.yml/badge.svg)](https://github.com/PennChopMicrobiomeProgram/CHOP_metadata_checker/actions/workflows/pr.yml)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/e0812479727e432fab23e154338f6acb)](https://app.codacy.com/gh/PennChopMicrobiomeProgram/CHOP_metadata_checker/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![codecov](https://codecov.io/gh/PennChopMicrobiomeProgram/CHOP_metadata_checker/graph/badge.svg?token=RZKFJ87M6U)](https://codecov.io/gh/PennChopMicrobiomeProgram/CHOP_metadata_checker)
[![DockerHub](https://img.shields.io/docker/pulls/ctbushman/metadata_checker)](https://hub.docker.com/repository/docker/ctbushman/metadata_checker/)

## Development

To start with local development:

```
git clone https://github.com/PennChopMicrobiomeProgram/CHOP_metadata_checker.git
cd CHOP_metadata_checker
python -m venv env/
source env/bin/activate
pip install -r requirements.txt
pip install -r dev-requirements.txt
pip install app/metadatalib/

create_metadata_test_db
export FLASK_DEBUG=1 && flask --app app/app run
```

## Deployment

How you want to deploy this will depend on your needs, facilities, and ability. We have it deployed by a Kubernetes cluster but you could also 1) just run it in development mode from a lab computer or 2) setup Nginx/Apache on a dedicated server or 3) run it serverlessly in the cloud (e.g. with [Zappa](https://github.com/zappa/Zappa) on AWS) or 4) do something else. There are lots of well documented examples of deploying Flask sites out there, look around and find what works best for you.

When running, it will default to using a SQLite3 database located in the root of this repository (automatically created if it doesn't already exist). You can change to a PostgreSQL backend by providing the environment variables METADATA_DB_HOST, METADATA_DB_NAME, METADATA_DB_USER, and METADATA_DB_PSWD. If you want to use a different backend, you'll have to do a bit of modification to ``app/metadatalib/src/metadatalib/__init__.py`` and be somewhat familiar with SQLAlchemy URI strings.

## Using the library

The `metadatalib` library can be installed and run anywhere by following the instructions in Development (you don't need to do the `create_metadata_test_db` and running the site (bottom two commands)). To connect it to a Postgres backend, you'll need to also set the environment variables `METADATA_DB_HOST`, `METADATA_DB_USER`, `METADATA_DB_NAME`, and `METADATA_DB_PSWD`.
