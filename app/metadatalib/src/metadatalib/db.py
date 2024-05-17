import psycopg2
import datetime

class MetadataDB(object):
    def __init__(self, host, user, password, db_name):
        self.conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname=db_name,
            port="5432"
        )

    
    def __del__(self):
        self.conn.close()

        
    def execute_sql_command(self, sql_command):
        print(sql_command)
        cur = self.conn.cursor()
        cur.execute(sql_command)
        self.conn.commit()
        ret = cur.fetchall()
        cur.close()
        return ret


    def db_setup(self):
        cur = self.conn.cursor()
        if cur.execute('SELECT table_name FROM information_schema.tables WHERE table_name=\'annotations\'') != 0:
            return
        else:
            cur.execute(open("schema.sql", "r").read())

    def create_project(self, project_name, contact_name, contact_email, code):
        sql_command = f'SELECT * FROM projects WHERE project_name={project_name}'
        project_exists = self.execute_sql_command(sql_command)
        if len(project_exists) > 0:
            sql_command = f'INSERT INTO projects (project_name, contact_name, contact_email, ticket_code) VALUES (\'{project_name}\', \'{contact_name}\', \'{contact_email}\', \'{code}\')'
            return self.execute_sql_command(sql_command)
    
    def create_annotation(self, sample_accession, attr, val):
        sql_command = f'INSERT INTO annotations (sample_accession, attr, val) VALUES ({sample_accession}, \'{attr}\', \'{val}\')'
        return self.execute_sql_command(sql_command)

    def create_annotations(self, annotations):
        sql_command = 'INSERT INTO annotations (sample_accession, attr, val) VALUES '
        sql_command += ', '.join([f'({s}, \'{a}\', \'{v}\')' for s, a, v in annotations])
        return self.execute_sql_command(sql_command)

    def create_sample(self, sample_name, submission_id, sample_type, subject_id, host_species):
        sql_command = f'INSERT INTO samples (sample_name, submission_id, sample_type, subject_id, host_species) VALUES (\'{sample_name}\', {submission_id}, \'{sample_type}\', \'{subject_id}\', \'{host_species}\')'
        self.execute_sql_command(sql_command)
    
        sql_command = f'SELECT sample_accession FROM samples WHERE sample_name=\'{sample_name}\' AND submission_id=\'{submission_id}\''
        return self.execute_sql_command(sql_command).strip()

    def create_samples(self, samples):
        sql_command = 'INSERT INTO samples (sample_name, submission_id, sample_type, subject_id, host_species) VALUES '
        sql_command += ', '.join([f'(\'{n}\', {s}, \'{t}\', \'{i}\', \'{h}\')' for n, s, t, i, h in samples])
        self.execute_sql_command(sql_command)

        sql_command = f'SELECT sample_accession FROM samples WHERE sample_name=\'{samples[0][0]}\' AND submission_id=\'{samples[0][1]}\''
        return int(self.execute_sql_command(sql_command).strip())

    def create_submission(self, project_id, comment):
        time_submitted = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        sql_command = f'INSERT INTO submissions (project_id, time_submitted, comment) VALUES ({project_id}, \'{time_submitted}\', \'{comment}\')'
        self.execute_sql_command(sql_command)

        sql_command = f'SELECT submission_id FROM submissions WHERE time_submitted=\'{time_submitted}\''
        return self.execute_sql_command(sql_command).strip()
    
    def project_hash_collision(self, code):
        sql_command = f'SELECT COUNT(*) FROM projects WHERE ticket_code=\'{code}\''
        result = self.execute_sql_command(sql_command)
        return int(result.strip()) > 0
    
    def get_project_from_project_code(self, code):
        sql_command = f'SELECT * FROM projects WHERE ticket_code=\'{code}\''
        res = self.execute_sql_command(sql_command)
        return res.strip().split("|")
