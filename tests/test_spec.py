from tablemusthave import Table
from tablemusthave.musthave import AllGood, DoesntApply, StillNeeds
from metadatalib.spec import allowed_file, specification
from metadatalib.table import run_fixes
import warnings


def test_allowed_file():
    assert allowed_file("test.tsv.gz") == False
    assert allowed_file("test.csv") == True
    assert allowed_file("test.xlsx") == False
    assert allowed_file("test") == False
    assert allowed_file("test.") == False
    assert allowed_file("test.txt") == True


# Tests for the specification are not even close to comprehensive, in this case I think it's better to just be very attentive to the code given its declarative nature instead of having a million tests that need to be rewritten every time the specification changes
def test_specification():
    for req, res in specification.check(Table(col_names, good_samples)):
        print(req.description())
        print(res.message())
        assert isinstance(res, AllGood) or isinstance(res, DoesntApply)


def test_empty_metadata():
    for req, res in specification.check(
        Table(
            col_names,
            [
                [
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ]
            ],
        )
    ):
        print(req.description())
        print(res.message())
        if isinstance(res, StillNeeds):
            return

    assert False


def test_bad_column_name():
    for bad in ["bad_column*%^", "bad,column"]:
        for req, res in specification.check(
            Table(col_names + [bad], [g + [""] for g in good_samples])
        ):
            print(req.description())
            print(res.message())
            if isinstance(res, StillNeeds):
                break
        else:
            assert False


def test_fix_column_name():
    t = Table(col_names + ["bad,column"], [g + ["val1"] for g in good_samples])
    run_fixes(t)
    assert "badcolumn" in t.colnames()


def test_empty_column_name_fix():
    t = Table(col_names + ["!!!"], [g + ["val1"] for g in good_samples])
    run_fixes(t)
    assert "unnamed_column" in t.colnames()


def test_overwrite_column_name_warning():
    t = Table(
        col_names + ["bad,column", "badcolumn"],
        [g + ["new1", "old1"] for g in good_samples],
    )
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        run_fixes(t)
        assert any("overwrites" in str(warn.message) for warn in w)
    assert t.get("badcolumn") == ["new1", "new1"]


col_names = [
    "SampleID",
    "sample_type",
    "subject_id",
    "host_species",
    "investigator",
    "plate",
    "plate_row",
    "plate_column",
    "date_collected",
    "time_collected",
    "BarcodeSequence",
]

good_samples = [
    [
        "Samply",
        "BAL",
        "subject1",
        "Dog",
        "investigator1",
        "plate1",
        "A",
        "1",
        "01-04-21",
        "12:00:00",
        "ATCG",
    ],
    [
        "AnotherOne",
        "Buffer",
        "subject2",
        "Fruit fly",
        "investigator2",
        "plate1",
        "A",
        "2",
        "06-07-23",
        "12:00:00",
        "TCGA",
    ],
]
