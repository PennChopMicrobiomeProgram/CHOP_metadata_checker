from tkinter import PROJECTING
from flask import Flask, render_template, url_for, request, redirect, flash, session, send_from_directory
import io, os
from werkzeug.utils import secure_filename
from tablemusthave import *
from db.db import MetadataDB
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
load_dotenv(Path.cwd() / '..' / 'CHOP.env')

ALLOWED_EXTENSIONS = {'tsv', 'csv'}

#check if period in filename and has correct extensions
def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

chop_mandatory_tube = [
  "SampleID",
  "investigator",
  "project_name",
  "sample_type",
  "tube_barcode",
  "box_id",
  "box_position",
  "study_group",
  "date_collected"
]

chop_suggested = [
  "subject_id",
  "host_species",
  "study_day",
  "current_antibiotics",
  "recent_antibiotics",
  "cage_id",
  "mouse_strain"
]

sample_type_list = [
  "Amnoitic fluid",
  "BAL",
  "Bedding",
  "Biofilm",
  "Bioreactor",
  "Blank swab",
  "Blood",
  "Breast milk",
  "Buffer",
  "Cecum",
  "Cell lysate",
  "Cervical swab",
  "Cheek swab",
  "Crop",
  "Dental plaque",
  "Duodenum",
  "Dust",
  "Elution buffer",
  "Empty well",
  "Endometrial swab",
  "Environmental control",
  "Esophageal biopsy",
  "Esophagus",
  "Feces",
  "Feed",
  "Fistula",
  "Fistula swab",
  "Fly food",
  "Fruit fly",
  "Ileostomy fluid",
  "Ileum",
  "Kveim reagent",
  "Lab water",
  "Macular Retina",
  "Meconium",
  "Medium",
  "Microbial culture",
  "Mock DNA",
  "Mouse chow",
  "Nasal swab",
  "Nasopharyngeal swab",
  "Oral swab",
  "Oral wash",
  "Oropharyngeal swab",
  "Ostomy fluid",
  "Pancreatic fluid",
  "PCR water",
  "Peripheral retina",
  "Placenta",
  "Plasma",
  "Rectal biopsy",
  "Rectal swab",
  "Saline",
  "Saliva",
  "Sediment",
  "Serum",
  "Skin swab",
  "Small intestine",
  "Soil",
  "Sputum",
  "Surface swab",
  "Tongue swab",
  "Tonsil",
  "Tracheal aspirate",
  "Tracheal control",
  "Urethral swab",
  "Urine",
  "Water",
  "Weighing paper",
  "Whole gut",
  "Large intestine mucosa",
  "Large intestine lumen",
]

host_species_list = [
  "Dog",
  "Fruit fly",
  "Human",
  "Mouse",
  "Naked mole rat",
  "Pig",	
  "Pigeon",
  "Rabbit",
  "Rat",
  "Rhesus macaque",
  None
]

##table to translate what these regex patterns mean
regex_translate = {
  "^[0-9A-Za-z._]+$": " only contain numbers, letters, underscores, and periods",
  "^[0-9A-Za-z_]+$": " only contain numbers, letters, and underscores",
  "^[A-Za-z]": " only start with capital or lowercase letters",
  "^[0-9A-Za-z._+-\/<>=|,() ]+$": " only contain numbers, letters, spaces, and allowed characters inside the bracket [._+-\/<>=|,()]",
  "^[0-9A-Za-z._-]+$": " only contain numbers, letters, periods, dashes, and underscores",
  "^[0-9]{2}/[0-9]{2}/[0-9]{2}$": " be in format mm/dd/yy",
  "^[0-9]{2}:[0-9]{2}:[0-9]{2}$": " be in format hh:mm:ss",
  "^[A-H][0-9]{2}$": " only contain a letter from A-H and a number 1-12",
  "^[ATCGURYKMSWBDHVN]+$": " only contain nucleotide symbols"
}

##function to check unique combinations for these column inputs
def uniq_comb(spec, col1, col2):
  spec.append(unique_values_for(col1, col2))
  spec.append(some_value_for(col1, col2))
  spec.append(unique_values_for(col2, col1))
  spec.append(some_value_for(col2, col1))

##specification is an object of MustHave class which contains other classes that checks table by calling a function that returns AllGood or StillNeeds class (DoesntApply class is called if no such column exists in the input)
specification = MustHave(
  columns_named(chop_mandatory_tube), ##must contain these columns
  columns_matching("^[0-9A-Za-z_]+$"), ##column names must satisfy this regex
  values_matching("SampleID", "^[A-Za-z]"), ##columns must satisfy this regex
  values_matching("SampleID", "^[0-9A-Za-z._]+$"),
  unique_values_for("SampleID"),
  values_in_set("sample_type", sample_type_list), ##sample_type column can only contain values specified in sample_type_list
  values_matching("subject_id", "^[A-Za-z]"),
  values_matching("subject_id", "^[0-9A-Za-z._-]+$"),
  values_in_set("host_species", host_species_list),
  some_value_for("host_species", "subject_id"),
  some_value_for("subject_id", "host_species"),
  some_value_for("mouse_strain", "cage_id"), ##if mouse_strain is given, a cage_id for that sample must be provided
  values_matching("date_collected", "^[0-9]{2}/[0-9]{2}/[0-9]{2}$"),
  values_matching("time_collected", "^[0-9]{2}:[0-9]{2}:[0-9]{2}$"),
  unique_values_for("barcode"),
  values_matching("barcode", "^[ATCGURYKMSWBDHVN]+$"),
  values_matching("reverse_barcode_location", "^[A-H][0-9]{2}$"),
  values_matching("forward_barcode_location", "^[A-H][0-9]{2}$"),
)

uniq_comb(specification, "box_id", "box_position")
uniq_comb(specification, "reverse_barcode_plate", "reverse_barcode_location")
uniq_comb(specification, "forward_barcode_plate", "forward_barcode_location")

specification.extend(some_value_for(c) for c in chop_mandatory_tube) ##these columns cannot be empty
specification.extend(values_matching(c, "^[0-9A-Za-z._+-/<>=,()\[\] ]+$") for c in (chop_mandatory_tube + chop_suggested)) ##all columns must satisfy the regex

for d in specification.descriptions():
  print(d)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
db_fp = os.environ.get('DB_FP')
t = Table([], []) # Declare as global var so it's accessible across pages easily

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
                              
@app.route('/wiki')
def wiki():
  return render_template('wiki.html')

@app.route('/review/<project_code>', methods=['GET', 'POST'])
def review(project_code):
  if request.method == 'POST':
    ##submit metadata
    db = MetadataDB(db_fp)
    ##create submission
    print(request.form['comment'])
    project_id = db.project_id_from_project_code(project_code)
    submission_id = db.create_submission(project_id, request.form['comment'])
    ##create samples
    cols = t.colnames()
    indeces = [cols.index('SampleID'), cols.index('sample_type'), cols.index('subject_id'), cols.index('host_species')]
    num_samples = len(t.get(cols[indeces[0]]))

    for i in range(num_samples):
      sample_id = db.create_sample(t.get_element('SampleID', i), submission_id, t.get_element('sample_type', i), t.get_element('subject_id', i), t.get_element('host_species', i))
      for j in range(len(cols)):
        ##create annotations
        if j not in indeces:
          if t.get_element(cols[j],i) != None:
            db.create_annotation(sample_id, cols[j], t.get_element(cols[j], i))
  
  return render_template('final.html', project_code=project_code)

@app.route('/<project_code>', methods=['GET', 'POST'])
def index(project_code):
  print(url_for('index', project_code=project_code))
  filename = "Select file ..."
  ##ideally we would have one db object for the whole app, seems like routes spawn their own threads though,
  ##which sqlite doesn't play nice with
  db = MetadataDB(db_fp)
  if not db.project_hash_collision(project_code):
    return render_template('dne.html', project_code=project_code)
  elif request.method == 'GET':
    return render_template('index.html', filename=filename, project_code=project_code)
  elif request.method == 'POST':
    ##check if post request has a file
    if 'metadata_upload' not in request.files:
      flash('Please select a file')
      return redirect(url_for('index', project_code=project_code))
    file_fp = request.files['metadata_upload']
    ##check if user submitted a file
    if file_fp.filename == '':
      flash('No file selected')
      return redirect(url_for('index', project_code=project_code))
    if file_fp and not allowed_file(file_fp.filename):
      filename = secure_filename(file_fp.filename)
      if(filename.rsplit('.', 1)[-1].lower() in ['xls', 'xlsx']):
        flash('Please export your excel file as .csv or .tsv first')
        return redirect(url_for('index', project_code=project_code))      
      else:
        flash('Please use the allowed file extensions for the metadata {.tsv, .csv}')
        return redirect(url_for('index', project_code=project_code))
    ##check if file was submitted and if it has correct extensions
    if file_fp and allowed_file(file_fp.filename):
      filename = secure_filename(file_fp.filename)
      delim = ','

      ##convert FileStorage to StringIO to read as csv/tsv object
      string_io = io.StringIO(file_fp.read().decode('utf-8-sig'), newline=None)
      if(filename.rsplit('.', 1)[1].lower() == 'tsv'):
        delim = '\t'

      global t
      t = Table.from_csv(string_io, delimiter = delim)
      
      ##get metadata table to print on webpage
      headers = t.colnames()
      sample_num = len(t.get(t.colnames()[0]))
      rows = list(range(0, sample_num))

      #overall check to see if metadata satisfies all requirements
      checks = specification.check(t)
      all_msg = [msg[1].message() for msg in checks]
      checks_passed = False
      print(all_msg)
      if(all(msg == 'OK' or "Doesn't apply" in msg for msg in all_msg)):
        flash('Your metadata is good to go!')
        checks_passed = True
      else:
        flash('Your metadata still has errors!')
        checks_passed = False

      ##create dictionaries for misformmated cell highlighting and popover text
      header_issues = {}
      highlight_missing = {}
      highlight_mismatch = {}
      highlight_repeating = {}
      highlight_not_allowed = {}
      
      ##print requirements and save the errors in the dictionarys to highlight in table
      for req, res in specification.check(t):
        if(isinstance(res, musthave.StillNeeds)):
          ##print(req.__dict__)
          ##print(res.__dict__)
          ##populate missing dictionary with empty cells
          if(res.idxs is not None):
            for row_num in res.idxs:
              for col_nam in req.colnames:
                if row_num in highlight_missing.keys():
                  highlight_missing = {**highlight_missing, **{row_num: highlight_missing[row_num] + [col_nam]}}
                else:
                  highlight_missing = {**highlight_missing, **{row_num: [col_nam]}}
            ##populate header dictionary for empty cell dictionary
            if len(req.colnames) == 1:
              header_issues = {**header_issues, **{req.colnames[0]: "Empty cell"}}
            ##populate header dictionary for unique cells between 2 or more columns
            else:
              header_issues = {**header_issues, **{req.colnames[0]: (" + ".join(req.colnames) + " must be filled in together")}}
          ##populate mismatch dictionary for illegally formmated cells (e.g. containing specials characters)
          if(res.not_matching is not None and hasattr(req, "colname")):
            highlight_mismatch = {**highlight_mismatch, **{cells : req.colname for cells in res.not_matching}}
            header_issues = {**header_issues, **{req.colname: "Wrong formatting"}}
          ##populate header dictionary with column names with wrong format
          if(res.not_matching is not None and not hasattr(req, "colname")):
            header_issues = {**header_issues, **{col_names: "Forbidden characters in column name" for col_names in res.not_matching}}
          ##populate repeating dictionary with repeating cells
          if(res.repeated is not None):
            highlight_repeating = {**highlight_repeating, **{cells[0][0] : req.colnames[0] for cells in res.repeated}}
            header_issues = {**header_issues, **{req.colnames[0]: "Repeated values"}}
          ##populate dictionary with cells that does not hold a pre-selected option
          if(res.not_allowed is not None):
            highlight_not_allowed = {**highlight_not_allowed, **{cells : req.colname for cells in res.not_allowed}}
            header_issues = {**header_issues, **{req.colname: "Use only allowed selections"}}
        ##print error messages
        if res.message() != 'OK' and "Doesn't apply" not in res.message():
          modified_descrip = req.description()[:-1]
          for keys in regex_translate.keys():
            if keys in req.description():
              modified_descrip = modified_descrip.split('match')[0] + regex_translate[keys]
          flash(modified_descrip + ": " + res.message())
      #print(highlight_repeating)
      return render_template('index.html', filename=filename, project_code=project_code, headers=headers, rows=rows, table=t, missing=highlight_missing, mismatch=highlight_mismatch, repeating=highlight_repeating, not_allowed=highlight_not_allowed, header_issues=header_issues, checks_passed=checks_passed)
    return redirect(url_for('index', project_code=project_code))

if __name__ == "__main__":
  app.run(debug=True)
