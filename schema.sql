-- Create the 'projects' table
CREATE TABLE IF NOT EXISTS projects (
  project_id SERIAL PRIMARY KEY,
  project_name TEXT NOT NULL UNIQUE,
  contact_name TEXT NOT NULL,
  contact_email TEXT NOT NULL,
  ticket_code TEXT NOT NULL UNIQUE
);

-- Create the 'submissions' table
CREATE TABLE IF NOT EXISTS submissions (
  submission_id SERIAL PRIMARY KEY,
  project_id INTEGER REFERENCES projects(project_id) ON UPDATE CASCADE ON DELETE CASCADE,
  version INTEGER,
  time_submitted TIMESTAMP NOT NULL,  -- Changed from TEXT to TIMESTAMP
  comment TEXT NOT NULL
);

-- Create the 'samples' table
CREATE TABLE IF NOT EXISTS samples (
  sample_accession SERIAL PRIMARY KEY,
  sample_name TEXT NOT NULL,
  submission_id INTEGER REFERENCES submissions(submission_id) ON UPDATE CASCADE ON DELETE CASCADE,
  sample_type TEXT DEFAULT NULL,
  subject_id TEXT DEFAULT NULL,
  host_species TEXT DEFAULT NULL
);

-- Create the 'annotations' table
CREATE TABLE IF NOT EXISTS annotations (
  sample_accession INTEGER REFERENCES samples(sample_accession) ON UPDATE CASCADE ON DELETE CASCADE,
  attr TEXT NOT NULL,
  val TEXT NOT NULL,
  PRIMARY KEY (sample_accession, attr)  -- Ensures each attribute per sample is unique
);