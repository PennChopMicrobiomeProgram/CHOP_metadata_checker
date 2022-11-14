import datetime
import sqlite3

class MetadataDB(object):
    def __init__(self, database_fp):
        self.db: str = database_fp
        self.con: sqlite3.Connection = sqlite3.connect(self.db)
    
    create_annotationQ = (
        "INSERT INTO annotations "
        "(`sample_accession`, `attr`, `val`) "
        "VALUES (?, ?, ?)")

    create_sampleQ = (
        "INSERT INTO samples "
        "(`sample_name`, `submission_id`, `sample_type`, `subject_id`, `host_species`)"
        "VALUES (?, ?, ?, ?, ?)")
    
    create_submissionQ = (
        "INSERT INTO submissions "
        "(`project_id`, `time_submitted`, `comment`) "
        "VALUES (?, ?, ?)")
    
    find_annotationQ = (
        "SELECT `sample_accession` "
        "FROM annotations "
        "WHERE `sample_accession`=? AND `attr`=? AND `val`=?")
    
    find_project_by_codeQ = (
        "SELECT * "
        "FROM projects "
        "WHERE `ticket_code`=?")
    
    find_sample_by_name_and_idQ = (
        "SELECT `sample_accession` "
        "fROM samples "
        "WHERE `sample_name`=? AND `submission_id`=?")
    
    find_submission_by_timeQ = (
        "SELECT `submission_id` "
        "FROM submissions "
        "WHERE `time_submitted`=?")

    # Creates a new annotation for a sample
    # @param sample_accession is the accession of the sample this annotation is for
    # @param attr is the attribute
    # @param val is the value
    # @return is the sample accession of the new annotation
    def create_annotation(self: object, sample_accession: int, attr: str, val: str):
        cur = self.con.cursor()
        cur.execute(self.create_annotationQ, (sample_accession, attr, val))
        self.con.commit()

        cur.execute(self.find_annotationQ, (sample_accession, attr, val))
        self.con.commit()
        res = cur.fetchall()
        cur.close()

        return res[0][0]
    
    # Creates a new sample for a submission
    # @param sample_name is the sample name
    # @param submission_id is the id of the submission this sample is a part of
    # @param sample_type is the sample type
    # @param subject_id is the subject id
    # @param host_species is the host species
    # @return is the accession of the new sample
    def create_sample(self: object, sample_name: str, submission_id: int, sample_type: str, subject_id: str, host_species: str) -> int:
        cur = self.con.cursor()
        cur.execute(self.create_sampleQ, (sample_name, submission_id, sample_type, subject_id, host_species))
        self.con.commit()

        cur.execute(self.find_sample_by_name_and_idQ, (sample_name, submission_id))
        self.con.commit()
        res = cur.fetchall()
        cur.close()

        return res[0][0]

    # Creates a new submission for a project
    # @param project_id is the id for the project this is a submission for
    # @param comment is the associated comment
    # @return is the id of the new submission
    def create_submission(self: object, project_id: int, comment: str) -> int:
        time_submitted = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        cur = self.con.cursor()
        cur.execute(self.create_submissionQ, (project_id, time_submitted, comment))
        self.con.commit()

        cur.execute(self.find_submission_by_timeQ, (time_submitted, ))
        self.con.commit()
        res = cur.fetchall()
        cur.close()

        return res[0][0]

    # Determine if the given project code already exists in the db
    # @param code is the project code to check for
    # @return is True if code already exists, False otherwise
    def project_hash_collision(self: object, code: str) -> bool:
        cur = self.con.cursor()
        cur.execute(self.find_project_by_codeQ, (code, ))
        self.con.commit()
        res = cur.fetchall()
        cur.close()
        
        if len(res) == 0:
            return False
        elif len(res) == 1:
            return True
        else:
            sqlite3.IntegrityError("Something's gone wrong, there shouldn't be more than one instance of ticket_code " + code + " in the projects table.")

    # Get a project's integer id from it's unique hex hash
    # @param code is the project hash
    # @return is the project's id
    def project_id_from_project_code(self: object, code: str) -> int:
        cur = self.con.cursor()
        cur.execute(self.find_project_by_codeQ, (code, ))
        self.con.commit()
        res = cur.fetchall()
        cur.close()

        return res[0][0]