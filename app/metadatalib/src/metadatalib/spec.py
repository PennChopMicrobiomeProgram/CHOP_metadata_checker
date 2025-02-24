from datetime import datetime
from tablemusthave import (
    unique_values_for,
    some_value_for,
    MustHave,
    Table,
    columns_named,
    columns_matching,
    values_matching,
    values_in_set,
)
from tablemusthave.musthave import (
    DoesntApply,
    must_have_result,
)
from metadatalib.consts import (
    ALLOWED_EXTENSIONS,
    CHOP_MANDATORY_TUBE,
    CHOP_SUGGESTED,
    SAMPLE_TYPE_LIST,
    HOST_SPECIES_LIST,
)


class no_leading_trailing_whitespace:
    def __init__(self, colname):
        self.colname = colname

    def description(self):
        desc = "Values of {0} must not have leading or trailing whitespace."
        return desc.format(self.colname)

    def check(self, t):
        if self.colname not in t:
            return DoesntApply(self.colname)
        vals = t.get(self.colname)
        not_matching = [v for v in vals if v and v.strip() != v]
        return must_have_result(not_matching=not_matching)

    def fix(self, t):
        t.data[self.colname] = [v.strip() if v else v for v in t.get(self.colname)]


# check if period in filename and has correct extensions
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


##function to check unique combinations for these column inputs
def uniq_comb(spec: MustHave, col1: str, col2: str):
    spec.append(unique_values_for(col1, col2))
    spec.append(some_value_for(col1, col2))
    spec.append(some_value_for(col2, col1))


def fix_date_collected(t: Table, colname: str, pattern: str):
    formats = [
        "%Y-%m-%d",  # 2024-02-24 (ISO format)
        "%d-%m-%Y",  # 24-02-2024
        "%m/%d/%Y",  # 02/24/2024 (US format)
        "%B %d, %Y",  # February 24, 2024
        "%b %d, %Y",  # Feb 24, 2024
        "%d %B %Y",  # 24 February 2024
        "%A, %d %B %Y",  # Saturday, 24 February 2024
        "%a %d %b %Y",  # Sat 24 Feb 2024
        "%Y-%j",  # 2024-055 (Year + Julian day)
        "%Y/%m/%d",  # 2024/02/24
        "%d/%m/%Y",  # 24/02/2024
        "%Y %U",  # 2024 08 (Year + Week number, Sunday start)
        "%Y %W",  # 2024 08 (Year + Week number, Monday start)
    ]

    def convert_date(date_string: str) -> str:
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt).strftime("%m-%d-%y")
            except ValueError:
                continue
        return date_string

    t.data[colname] = [convert_date(v) for v in t.get(colname)]


def fix_time_collected(t: Table, colname: str, pattern: str):
    formats = [
        "%H:%M:%S",  # 24-hour format (HH:MM:SS)
        "%I:%M:%S %p",  # 12-hour format with AM/PM (HH:MM:SS AM/PM)
        "%H:%M",  # 24-hour format (HH:MM)
        "%I:%M %p",  # 12-hour format with AM/PM (HH:MM AM/PM)
        "%H:%M:%S.%f",  # 24-hour format with microseconds (HH:MM:SS.ssssss)
        "%I:%M:%S.%f %p",  # 12-hour format with microseconds (HH:MM:SS.ssssss AM/PM)
    ]

    def convert_time(time_string: str) -> str:
        for fmt in formats:
            try:
                return datetime.strptime(time_string, fmt).strftime("%H:%M:%S")
            except ValueError:
                continue
        return time_string

    t.data[colname] = [convert_time(v) for v in t.get(colname)]


##specification is an object of MustHave class which contains other classes that checks table by calling a function that returns AllGood or StillNeeds class (DoesntApply class is called if no such column exists in the input)
specification: MustHave = MustHave(
    # no_leading_trailing_whitespace(),
    columns_named(CHOP_MANDATORY_TUBE),  ##must contain these columns
    columns_matching("^[0-9A-Za-z_.]+$"),  ##column names must satisfy this regex
    values_matching("SampleID", "^[A-Za-z]"),  ##columns must satisfy this regex
    values_matching("SampleID", "^[0-9A-Za-z._]+$"),
    unique_values_for("SampleID"),
    values_in_set(
        "sample_type", SAMPLE_TYPE_LIST
    ),  ##sample_type column can only contain values specified in SAMPLE_TYPE_LIST
    values_matching("subject_id", "^[A-Za-z]"),
    values_matching("subject_id", "^[0-9A-Za-z._-]+$"),
    values_in_set("host_species", HOST_SPECIES_LIST),
    some_value_for("host_species", "subject_id"),
    some_value_for("subject_id", "host_species"),
    some_value_for(
        "mouse_strain", "cage_id"
    ),  ##if mouse_strain is given, a cage_id for that sample must be provided
    values_matching(
        "date_collected", "^[0-9]{2}-[0-9]{2}-[0-9]{2}$", fix_fn=fix_date_collected
    ),
    values_matching(
        "time_collected", "^[0-9]{2}:[0-9]{2}:[0-9]{2}$", fix_fn=fix_time_collected
    ),
    unique_values_for("barcode"),
    values_matching("barcode", "^[ATCGURYKMSWBDHVN]+$"),
    values_matching("reverse_barcode_location", "^[A-H][0-9]{2}$"),
    values_matching("forward_barcode_location", "^[A-H][0-9]{2}$"),
)

uniq_comb(specification, "tube_id", "box_id")
uniq_comb(specification, "box_id", "box_position")
uniq_comb(specification, "reverse_barcode_plate", "reverse_barcode_location")
uniq_comb(specification, "forward_barcode_plate", "forward_barcode_location")

specification.extend(
    some_value_for(c) for c in CHOP_MANDATORY_TUBE
)  ##these columns cannot be empty
specification.extend(
    values_matching(c, "^[0-9A-Za-z._+-/<>=,()\[\] ]+$")
    for c in (CHOP_MANDATORY_TUBE + CHOP_SUGGESTED)
)  ##all columns must satisfy the regex
