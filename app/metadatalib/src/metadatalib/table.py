from tablemusthave import Table, StillNeeds, MustHave
from typing import Callable
from metadatalib.spec import no_leading_trailing_whitespace, specification
from metadatalib.consts import REGEX_TRANSLATE


try:
    from flask import flash
except ImportError:

    def flash(msg):
        pass


def run_checks(
    t: Table,
    specification: MustHave = specification,
    flash: Callable[[str], None] = flash,
) -> tuple[Table, dict]:
    # Get metadata table to print on webpage
    headers = t.colnames()
    sample_num = len(t.get(t.colnames()[0]))
    rows = list(range(0, sample_num))

    for h in headers:
        specification.append(no_leading_trailing_whitespace(h))

    # Overall check to see if metadata satisfies all requirements
    checks = specification.check(t)
    all_msg = [msg[1].message() for msg in checks]
    checks_passed = False
    if all(msg == "OK" or "Doesn't apply" in msg for msg in all_msg):
        checks_passed = True

    # Create dictionaries for misformmated cell highlighting and popover text
    header_issues = {}
    highlight_missing = {}
    highlight_mismatch = {}
    highlight_repeating = {}
    highlight_not_allowed = {}

    ##print requirements and save the errors in the dictionarys to highlight in table
    for req, res in specification.check(t):
        if isinstance(res, StillNeeds):
            ##print(req.__dict__)
            ##print(res.__dict__)
            ##populate missing dictionary with empty cells
            if res.idxs is not None:
                for row_num in res.idxs:
                    for col_nam in req.colnames:
                        if row_num in highlight_missing.keys():
                            highlight_missing = {
                                **highlight_missing,
                                **{row_num: highlight_missing[row_num] + [col_nam]},
                            }
                        else:
                            highlight_missing = {
                                **highlight_missing,
                                **{row_num: [col_nam]},
                            }
                ##populate header dictionary for empty cell dictionary
                if len(req.colnames) == 1:
                    header_issues = {**header_issues, **{req.colnames[0]: "Empty cell"}}
                ##populate header dictionary for unique cells between 2 or more columns
                else:
                    header_issues = {
                        **header_issues,
                        **{
                            req.colnames[0]: (
                                " + ".join(req.colnames) + " must be filled in together"
                            )
                        },
                    }
            ##populate mismatch dictionary for illegally formmated cells (e.g. containing specials characters)
            if res.not_matching is not None and hasattr(req, "colname"):
                highlight_mismatch = {
                    **highlight_mismatch,
                    **{cells: req.colname for cells in res.not_matching},
                }
                header_issues = {**header_issues, **{req.colname: "Wrong formatting"}}
            ##populate header dictionary with column names with wrong format
            if res.not_matching is not None and not hasattr(req, "colname"):
                header_issues = {
                    **header_issues,
                    **{
                        col_names: "Forbidden characters in column name"
                        for col_names in res.not_matching
                    },
                }
            ##populate repeating dictionary with repeating cells
            if res.repeated is not None:
                highlight_repeating = {
                    **highlight_repeating,
                    **{cells[0][0]: req.colnames[0] for cells in res.repeated},
                }
                header_issues = {
                    **header_issues,
                    **{req.colnames[0]: "Repeated values"},
                }
            ##populate dictionary with cells that does not hold a pre-selected option
            if res.not_allowed is not None:
                highlight_not_allowed = {
                    **highlight_not_allowed,
                    **{cells: req.colname for cells in res.not_allowed},
                }
                header_issues = {
                    **header_issues,
                    **{req.colname: "Use only allowed selections"},
                }
        ##print error messages
        if res.message() != "OK" and "Doesn't apply" not in res.message():
            modified_descrip = req.description()[:-1]
            for keys in REGEX_TRANSLATE.keys():
                if keys in req.description():
                    modified_descrip = (
                        modified_descrip.split("match")[0] + REGEX_TRANSLATE[keys]
                    )

            flash(modified_descrip + ": " + res.message())

    return (
        t,
        {
            "headers": headers,
            "rows": rows,
            "missing": highlight_missing,
            "mismatch": highlight_mismatch,
            "repeating": highlight_repeating,
            "not_allowed": highlight_not_allowed,
            "header_issues": header_issues,
            "passed": checks_passed,
        },
    )


def run_fixes(t: Table, specification: MustHave = specification):
    for h in t.colnames():
        specification.append(no_leading_trailing_whitespace(h))
    specification.fix(t)
