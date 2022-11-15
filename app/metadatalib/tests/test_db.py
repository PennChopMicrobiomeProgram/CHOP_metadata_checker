import os
import shutil
import subprocess
import tempfile
import unittest

from pathlib import Path
from src.db import MetadataDB

from dotenv import load_dotenv
load_dotenv(Path.cwd() / '../../CHOP.env')

class MetadataDBTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db = MetadataDB(":memory:")

        self.schema_fp = Path.cwd() / "../../schema.sql"
        with open(self.schema_fp, "rt") as f:
            schema = f.read()
        self.db.con.executescript(schema)

        create_projectQ = (
        "INSERT INTO projects "
        "(`project_name`, `contact_name`, `contact_email`, `ticket_code`) "
        "VALUES (?, ?, ?, ?)")

        cur = self.db.con.cursor()
        cur.execute(create_projectQ, ("project_name", "contact_name", "contact_email", "EXISTS", ))
        self.db.con.commit()
        cur.close()

    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_project_hash_collision(self):
        self.assertFalse(self.db.project_hash_collision("DOESN'T EXIST"))
        self.assertTrue(self.db.project_hash_collision("EXISTS"))

    def test_project_id_from_project_code(self):
        self.assertEqual(1, self.db.project_id_from_project_code("EXISTS"))
    
    def test_create_submission(self):
        self.assertEqual(1, self.db.create_submission(1, "COMMENT"))

    def test_create_sample(self):
        self.assertEqual(1, self.db.create_sample("SAMPLE", 1, "TYPE", "SUBJECT", "HOST"))

    def test_create_annotation(self):
        self.assertEqual(1, self.db.create_annotation(1, "ATTR", "VAL"))