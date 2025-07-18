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


common_specs = [
    columns_matching("^[0-9A-Za-z_-]+$", fix_fn=fix_column_names),
    values_matching("SampleID", "^[A-Za-z]", fix_fn=fix_sample_start),
    values_matching("SampleID", "^[0-9A-Za-z._]+$", fix_fn=fix_disallowed_sample_chars),
    unique_values_for("SampleID"),
    values_matching("subject_id", "^[A-Za-z]", fix_fn=fix_subject_start),
    values_matching(
        "subject_id", "^[0-9A-Za-z._-]+$", fix_fn=fix_disallowed_sample_chars
    ),
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
]

tube_specs = [
    columns_named(CHOP_MANDATORY_TUBE),
    values_in_set("sample_type", SAMPLE_TYPE_LIST),
    values_in_set("host_species", HOST_SPECIES_LIST),
    some_value_for("host_species", "subject_id"),
    some_value_for("subject_id", "host_species"),
    some_value_for("mouse_strain", "cage_id"),
    unique_values_for("tube_id", "box_id"),
    unique_values_for("box_id", "box_position"),
    unique_values_for("reverse_barcode_plate", "reverse_barcode_location"),
    unique_values_for("forward_barcode_plate", "forward_barcode_location"),
    some_value_for("tube_id", "box_id"),
    some_value_for("box_id", "tube_id"),
    some_value_for("box_id", "box_position"),
    some_value_for("box_position", "box_id"),
    some_value_for("reverse_barcode_plate", "reverse_barcode_location"),
    some_value_for("reverse_barcode_location", "reverse_barcode_plate"),
    some_value_for("forward_barcode_plate", "forward_barcode_location"),
    some_value_for("forward_barcode_location", "forward_barcode_plate"),
    *(some_value_for(c) for c in CHOP_MANDATORY_TUBE),
    *(
        values_matching(c, "^[0-9A-Za-z._+-/<>=,()\[\] ]+$")
        for c in (CHOP_MANDATORY_TUBE + CHOP_SUGGESTED)
    ),
]

# Looser checks for internal samples, used in automation for munging metadata and merging barcodes
internal_specs = [
    columns_named(["SampleID", "sample_type"]),
    unique_values_for("plate", "plate_row", "plate_column"),
    some_value_for("plate", "plate_row"),
    some_value_for("plate", "plate_column"),
]


specification = MustHave(*common_specs, *tube_specs)
internal_specification = MustHave(*common_specs, *internal_specs)
