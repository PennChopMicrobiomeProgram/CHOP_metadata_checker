import argparse
import csv
import os
import shutil
import sys

def _create_project(args):
    print(type(args))

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("project_name", help="Name of the project")
    p.add_argument("customer_name", help="Name of the customer")

    args = p.parse_args(argv)

    None if os.path.isdir("logs/") else os.mkdir("logs")
    logF = open("logs/main.log", "w")
    print("Writing logs to: " + logF.name)

    _create_project(args)