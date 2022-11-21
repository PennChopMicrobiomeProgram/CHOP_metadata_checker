#!/bin/bash

source env/bin/activate

pip install app/metadatalib/

zappa update dev
