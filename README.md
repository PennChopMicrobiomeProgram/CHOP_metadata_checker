# MetadataChecker

A Flask site for validating metadata sheets per the standards of the PCMP and an associated library for project management.

[![Tests](https://github.com/PennChopMicrobiomeProgram/CHOP_metadata_checker/actions/workflows/pr.yml/badge.svg)](https://github.com/PennChopMicrobiomeProgram/CHOP_metadata_checker/actions/workflows/pr.yml)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/e0812479727e432fab23e154338f6acb)](https://app.codacy.com/gh/PennChopMicrobiomeProgram/CHOP_metadata_checker/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![codecov](https://codecov.io/gh/PennChopMicrobiomeProgram/CHOP_metadata_checker/graph/badge.svg?token=RZKFJ87M6U)](https://codecov.io/gh/PennChopMicrobiomeProgram/CHOP_metadata_checker)
[![DockerHub](https://img.shields.io/docker/pulls/ctbushman/metadata_checker)](https://hub.docker.com/repository/docker/ctbushman/metadata_checker/)

## Development

This is a Flask app leveraging with bootstrap, jquery, and datatables (via CDN). To start with local development:

```
git clone https://github.com/PennChopMicrobiomeProgram/CHOP_metadata_checker.git
cd CHOP_metadata_checker
python -m venv env/
source env/bin/activate
pip install -e .[dev,web]

export METADATA_DB_URI=sqlite:///db.sqlite3
create_metadata_test_db
python metadatalib/app.py
```

`create_metadata_test_db` will create a couple projects with ids `1` and `2`. Feel free to `sqlite3 metadata.sqlite3` to examine the test data more closely.

### Development with Docker

To run the app locally in a docker container instead:

```
docker run --rm -p 8080:80 ctbushman/metadata_checker:latest
```

You should then be able to access the site at http://localhost:8080. To build your own container:

```
git clone https://github.com/PennChopMicrobiomeProgram/CHOP_metadata_checker.git
cd CHOP_metadata_checker
docker build -t myrepo/metadata_checker:dev -f Dockerfile .
docker run --rm -p 8080:80 myrepo/metadata_checker:dev
```

The downside to this method of development is that you have to rebuild the container to see changes (or else do your dev work within the container as well, see VS Code Dev Containers), but it can act as a good check that your changes will work in the dockerized version of your deployment before you push to a docker-based hosting environment.

## Deployment

How you want to deploy this will depend on your needs, facilities, and ability. We have it deployed by a Kubernetes cluster but you could also 1) just run it in development mode from a lab computer or 2) setup Nginx/Apache on a dedicated server or 3) run it serverlessly in the cloud (e.g. with [Zappa](https://github.com/zappa/Zappa) on AWS) or 4) do something else. There are lots of well documented examples of deploying Flask sites out there, look around and find what works best for you.

When running, it will default to using a SQLite3 database located in the root of this repository (automatically created if it doesn't already exist). You can update it to use whatever backend you want by setting the `METADATA_DB_URI` environment variable before running the app. This URI is a SQL Alchemy connection URI, so you may want to do some research to figure out what you need to specify to connect to your preferred database instance. For another SQLite instance, for example, use `export METADATA_DB_URI=sqlite:////path/to/db.sqlite3`. For more complex databases you may have to install helper libraries for SQL Alchemy to establish the connection.

## Using the library

The `metadatalib` library can be installed and run anywhere by following the instructions in Development (you don't need to do the `create_metadata_test_db` and running the site (bottom two commands)). To connect to a non-dev backend, see the above on SQL Alchemy URIs.
