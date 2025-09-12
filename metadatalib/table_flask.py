# Keeping this separate to avoid importing flask/werkzeug in externally available functions
import io
from tablemusthave.table import Table
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


def table_from_file(file_fp: FileStorage) -> Table:
    filename = secure_filename(str(file_fp.filename))
    delim = ","

    # Convert FileStorage to StringIO to read as csv/tsv object
    string_io = io.StringIO(file_fp.read().decode("utf-8-sig"), newline=None)
    if filename.rsplit(".", 1)[1].lower() in ["tsv", "txt"]:
        delim = "\t"

    return Table.from_csv(string_io, delimiter=delim)
