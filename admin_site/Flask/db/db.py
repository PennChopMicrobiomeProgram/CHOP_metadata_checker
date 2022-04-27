import sqlite3
import sys

class MetadataDB(object):
    def __init__(self, database_fp):
        self.db: str = database_fp
        self.con: sqlite3.Connection = sqlite3.connect(self.db)
    
    create_projectQ = (
        "INSERT INTO projects "
        "(`project_name`, `contact_name`, `contact_email`, `ticket_code`) "
        "VALUES (?, ?, ?, ?)")
    
    get_projectQ = (
        "SELECT * "
        "FROM projects "
        "WHERE `project_name`=?")
    
    find_project_by_codeQ = (
        "SELECT * "
        "FROM projects "
        "WHERE `ticket_code`=?")

    list_projectsQ = (
        "SELECT * "
        "FROM projects")

    list_submissionsQ = (
        "SELECT * "
        "FROM submissions "
        "WHERE `project_id`=?")

    # Creates a new project in the db
    # @param project_name is the project name
    # @param contact_name is the contact name
    # @param contact_email is the contact email
    # @param code is the project code
    def create_project(self: object, project_name: str, contact_name: str, contact_email: str, code: str):
        cur = self.con.cursor()
        try:
            cur.execute(self.create_projectQ, (project_name, contact_name, contact_email, code, ))
        except sqlite3.IntegrityError as e:
            print(e)
            cur.execute(self.get_projectQ, (project_name, ))
            self.con.commit()
            res = cur.fetchall()
            if len(res) > 0:
                print(str(res[0]) + " already exists")
                sys.exit()
        self.con.commit()
        cur.close()

    # List projects in the db
    # @return is the list of projects
    def list_projects(self: object) -> list:
        cur = self.con.cursor()
        cur.execute(self.list_projectsQ)
        self.con.commit()
        return cur.fetchall()

    # List submissions in the db for a given project
    # @param code is the code for the project
    # @return is the list of submissions for that project
    def list_submissions(self: object, code: str) -> list:
        cur = self.con.cursor()
        cur.execute(self.list_submissionsQ, (code, ))
        self.con.commit()
        return cur.fetchall()
    
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