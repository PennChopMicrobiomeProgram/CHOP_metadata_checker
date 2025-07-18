# Dear agents,

## Structure

This repo is two distinct pieces of software. The Flask app is for user interactions and lives in `app/`. The metadatalib is a Python library that provides essential functions for the Flask app and lives under `app/metadatalib/`.

## Contributing

Lint with `black .` and test with `pytest app/metadatalib/tests`.

## metadatalib

This library is used to check/fix metadata sheets and store submissions in a database. The check/fix functionality should be kept separate enough from the Flask/database interactions that it can be imported and used in other applications.
