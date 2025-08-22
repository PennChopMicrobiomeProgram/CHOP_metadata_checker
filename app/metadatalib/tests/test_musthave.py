from tablemusthave import Table
from src.metadatalib.musthave import (
    fix_disallowed_sample_chars,
    fix_subject_start,
    fix_sample_start,
)


def test_fix_subject_start_skips_na_values():
    t = Table(
        ["subject_id"],
        [
            [None],
            ["1"],
            ["subject1"],
        ],
    )
    fix_subject_start(t, "subject_id", "^[A-Za-z]")
    assert t.get("subject_id") == [None, "SB1", "subject1"]


def test_fix_sample_start_skips_na_values():
    t = Table(
        ["SampleID"],
        [
            [None],
            ["1"],
            ["SampleA"],
        ],
    )
    fix_sample_start(t, "SampleID", "^[A-Za-z]")
    assert t.get("SampleID") == [None, "S1", "SampleA"]


def test_fix_disallowed_sample_chars_skips_na_values():
    t = Table(
        ["subject_id"],
        [
            [None],
            ["Subject1"],
            ["Subject@2"],
        ],
    )
    fix_disallowed_sample_chars(t, "subject_id", "^[0-9A-Za-z_.-]")
    assert t.get("subject_id") == [None, "Subject1", "Subject.2"]
