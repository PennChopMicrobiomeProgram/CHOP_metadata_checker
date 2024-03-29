CREATE TABLE IF NOT EXISTS projects (
  project_id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_name TEXT NOT NULL UNIQUE,
  contact_name TEXT NOT NULL,
  contact_email TEXT NOT NULL,
  ticket_code TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS submissions (
  submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER
    REFERENCES projects(project_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  version INTEGER,
  time_submitted TEXT NOT NULL,
  comment TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS samples (
  sample_accession INTEGER PRIMARY KEY AUTOINCREMENT,
  sample_name TEXT NOT NULL,
  submission_id INTEGER
    REFERENCES submissions(submission_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  sample_type TEXT DEFAULT NULL,
  subject_id TEXT DEFAULT NULL,
  host_species TEXT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS annotations (
  sample_accession INTEGER
    REFERENCES samples(sample_accession)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  attr TEXT NOT NULL,
  val TEXT NOT NULL
);
