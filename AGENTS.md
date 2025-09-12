# Dear agents,

## Structure

This repo contains a single Python library `metadatalib` with a Flask app in `metadatalib/app.py`. Static assets and templates live in `metadatalib/static` and `metadatalib/templates`.

## Contributing

Lint with `black .` and test with `pytest tests`.

## metadatalib

This library is used to check/fix metadata sheets and store submissions in a database. The check/fix functionality should remain separate enough from the Flask/database interactions that it can be imported and used in other applications.
