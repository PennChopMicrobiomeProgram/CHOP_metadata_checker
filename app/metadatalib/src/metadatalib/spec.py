from tablemusthave import (
    unique_values_for,
    some_value_for,
    MustHave,
    columns_named,
    columns_matching,
    values_matching,
    values_in_set,
)
from tablemusthave.musthave import must_have_result, DoesntApply
from metadatalib.consts import (
    ALLOWED_EXTENSIONS,
    CHOP_MANDATORY_TUBE,
    CHOP_SUGGESTED,
    SAMPLE_TYPE_LIST,
    HOST_SPECIES_LIST,
)
from metadatalib.musthave import (
    fix_date_collected,
    fix_disallowed_sample_chars,
    fix_column_names,
    fix_sample_start,
    fix_subject_start,
    fix_time_collected,
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
        if t.get(self.colname):
            t.data[self.colname] = [v.strip() if v else v for v in t.get(self.colname)]


# check if period in filename and has correct extensions
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


specs_common = [
    columns_named(
        [
            "SampleID",
            "subject_id",
            "investigator",
            "plate",
            "plate_row",
            "plate_column",
            "date_collected",
            "time_collected",
            "BarcodeSequence",
        ]
    ),
    columns_matching("^[0-9A-Za-z_.-]+$", fix_fn=fix_column_names),
    values_matching("SampleID", "^[A-Za-z]", fix_fn=fix_sample_start),
    values_matching("SampleID", "^[0-9A-Za-z._]+$", fix_fn=fix_disallowed_sample_chars),
    unique_values_for("SampleID"),
    values_matching("subject_id", "^[A-Za-z]", fix_fn=fix_subject_start),
    values_matching(
        "subject_id", "^[0-9A-Za-z._-]+$", fix_fn=fix_disallowed_sample_chars
    ),
    unique_values_for("plate", "plate_row", "plate_column"),
    values_matching(
        "date_collected", "^[0-9]{2}-[0-9]{2}-[0-9]{2}$", fix_fn=fix_date_collected
    ),
    values_matching(
        "time_collected", "^[0-9]{2}:[0-9]{2}:[0-9]{2}$", fix_fn=fix_time_collected
    ),
    unique_values_for("BarcodeSequence"),
    values_matching("BarcodeSequence", "^[ATCGURYKMSWBDHVN]+$"),
]

specs_common_strict = [
    columns_named(
        [
            "sample_type",
            "host_species",
        ]
    ),
    values_in_set("sample_type", SAMPLE_TYPE_LIST),
    values_in_set("host_species", HOST_SPECIES_LIST),
    some_value_for("host_species", "subject_id"),
    some_value_for("subject_id", "host_species"),
]

specs_16S = [
    columns_named(
        [
            "reverse_barcode_plate",
            "reverse_barcode_location",
            "forward_barcode",
        ]
    ),
    values_matching("reverse_barcode_plate", "^[A-Z][0-9]{1,2}$"),
    some_value_for("reverse_barcode_location"),
    some_value_for("forward_barcode"),
]

specs_ITS = [
    columns_named(
        [
            "reverse_barcode_plate",
            "reverse_barcode_location",
            "forward_barcode",
        ]
    ),
    values_matching("reverse_barcode_plate", "^[A-Z][0-9]{1,2}$"),
    some_value_for("reverse_barcode_location"),
    some_value_for("forward_barcode"),
]

specs_UDI = [
    columns_named(
        [
            "Primer_version",
            "barcode_index_set",
            "barcode_coord",
        ]
    ),
    values_in_set("Primer_version", ["v1", "v2", "v3", "v4"]),
    values_matching("barcode_index_set", "^UDI Set [A-D]$"),
    values_matching("barcode_coord", "^[A-H][0-9]{1,2}$"),
]

specification = MustHave(*specs_common, *specs_common_strict)
internal_specification = MustHave(*specs_common)

