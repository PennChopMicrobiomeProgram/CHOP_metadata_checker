from tablemusthave import Table
from tablemusthave.musthave import AllGood, DoesntApply, StillNeeds
from src.metadatalib.spec import allowed_file, specification


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
            [[None, None, None, None, None, None, None, None, None, None, None]],
        )
    ):
        print(req.description())
        print(res.message())
        if isinstance(res, StillNeeds):
            return

    assert False


def test_bad_column_name():
    for req, res in specification.check(
        Table(col_names + ["bad_column*%^"], [g + [""] for g in good_samples])
    ):
        print(req.description())
        print(res.message())
        if isinstance(res, StillNeeds):
            return

    assert False


col_names = [
    "SampleID",
    "sample_type",
    "subject_id",
    "host_species",
    "investigator",
    "project_name",
    "tube_id",
    "box_id",
    "box_position",
    "study_group",
    "date_collected",
]

good_samples = [
    [
        "Samply",
        "BAL",
        "subject1",
        "Dog",
        "investigator1",
        "project1",
        "tube1",
        "box1",
        "position1",
        "group1",
        "01-04-21",
    ],
    [
        "AnotherOne",
        "Buffer",
        "subject2",
        "Fruit fly",
        "investigator2",
        "project2",
        "tube2",
        "box2",
        "position2",
        "group2",
        "06-07-23",
    ],
]
