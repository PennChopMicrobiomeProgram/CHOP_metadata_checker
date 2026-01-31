import csv
import io
import urllib.request
from typing import Optional

ALLOWED_EXTENSIONS: set[str] = {"tsv", "csv", "txt"}

DEFAULT_SAMPLE_FIELDS: list[str] = [
    "SampleID",
    "sample_type",
    "subject_id",
    "host_species",
]

CHOP_MANDATORY_TUBE: list[str] = [
    "SampleID",
    "investigator",
    "sample_type",
]

CHOP_SUGGESTED: list[str] = [
    "subject_id",
    "host_species",
    "study_day",
    "current_antibiotics",
    "recent_antibiotics",
    "cage_id",
    "mouse_strain",
]

SAMPLE_TYPES_URL = (
    "https://raw.githubusercontent.com/PennChopMicrobiomeProgram/"
    "SampleRegistry/master/sample_registry/data/standard_sample_types.tsv"
)
HOST_SPECIES_URL = (
    "https://raw.githubusercontent.com/PennChopMicrobiomeProgram/"
    "SampleRegistry/master/sample_registry/data/standard_host_species.tsv"
)


def _fetch_tsv_column(url: str, column_name: str) -> list[str]:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode("utf-8")
    except Exception as exc:
        print(f"Warning: failed to fetch {url}: {exc}")
        return []
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    values = []
    for row in reader:
        value = row.get(column_name)
        if value is None:
            continue
        value = value.strip()
        if not value:
            continue
        values.append(value)
    return values


SAMPLE_TYPE_LIST: list[str] = _fetch_tsv_column(SAMPLE_TYPES_URL, "sample_type")
optional_host_species = _fetch_tsv_column(HOST_SPECIES_URL, "host_species")
optional_host_species.append(None)
HOST_SPECIES_LIST: Optional[list[str]] = optional_host_species

##table to translate what these regex patterns mean
REGEX_TRANSLATE: dict[str, str] = {
    "^[0-9A-Za-z._]+$": " only contain numbers, letters, underscores, and periods",
    "^[0-9A-Za-z_]+$": " only contain numbers, letters, and underscores",
    "^[A-Za-z]": " only start with capital or lowercase letters",
    "^[0-9A-Za-z._+-\/<>=|,() ]+$": " only contain numbers, letters, spaces, and allowed characters inside the bracket [._+-\/<>=|,()]",
    "^[0-9A-Za-z._-]+$": " only contain numbers, letters, periods, dashes, and underscores",
    "^[0-9]{2}/[0-9]{2}/[0-9]{2}$": " be in format mm/dd/yy",
    "^[0-9]{2}:[0-9]{2}:[0-9]{2}$": " be in format hh:mm:ss",
    "^[A-H][0-9]{2}$": " only contain a letter from A-H and a number 1-12",
    "^[ATCGURYKMSWBDHVN]+$": " only contain nucleotide symbols",
}
