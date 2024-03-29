import os
import shutil
import subprocess
import tempfile
import unittest

from pathlib import Path
from src.metadatacli.db import MetadataDB

from dotenv import load_dotenv
SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SRC_ROOT, '../../CHOP.env'))

class MetadataDBTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db = MetadataDB(":memory:")

        self.schema_fp = os.path.join(SRC_ROOT, '../../schema.sql')
        with open(self.schema_fp, "rt") as f:
            schema = f.read()
        self.db.con.executescript(schema)

    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_project_hash_collision(self):
        self.assertFalse(self.db.project_hash_collision("DOESN'T EXIST"))

    def test_create_project(self):
        self.db.create_project("PROJ_NAME", "CLIENT_NAME", "EMAIL", "EXISTS")
        self.assertTrue(self.db.project_hash_collision("EXISTS"))