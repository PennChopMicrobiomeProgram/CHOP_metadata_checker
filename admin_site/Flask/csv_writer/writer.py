from db.db import MetadataDB

# Helper function for generating a csv string for flask to download
# @param project_id is the id of the project to download
# @param submission_id is the id of the submissions to download
# @return is the csv in string form for flask to output
def generate_csv(db: MetadataDB, project_id: int, submission_id: int) -> str:
    return """
    "REVIEW_DATE","AUTHOR","ISBN","DISCOUNTED_PRICE"
    "1985/01/21","Douglas Adams",0345391802,5.95
    "1990/01/12","Douglas Hofstadter",0465026567,9.95
    "1998/07/15","Timothy ""The Parser"" Campbell",0968411304,18.99
    "1999/12/03","Richard Friedman",0060630353,5.95
    "2004/10/04","Randel Helms",0879755725,4.50
    """
