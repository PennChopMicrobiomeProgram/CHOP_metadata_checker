# MetaReady — Google Sheets Editor add-on

One centrally maintained add-on works with each project's existing shared Google Sheet. The source is local; Google deployment is described in [DEPLOYMENT.md](DEPLOYMENT.md).

## Customer submission formats

- **Tube_format:** accepts the customer headers SampleID, investigator, project_name, tube_barcode, box_id, box_position, sample_type, subject_id, host_species, study_day, study_group, current_antibiotics, year_collected, time_collected, mouse_strain, cage_id and Sex. Extra fields are retained; existing validation rules apply where defined. Both customer templates use sample_type and year_collected. Legacy SampleType remains a compatibility alias. This workflow adds controls using the R template and creates metadata_originally_submitted, metadata and plate_review.
- **Plate Template:** samples and controls are already positioned. The addControls workflow detects this format automatically; no format selector is shown. The preparation button automatically recognizes plate-position columns (or the Plate Template tab name). It validates and creates only **metadata_originally_submitted** and **plate_view**. The source is retained, and the snapshot freezes its submitted values. No IDs, controls, headers or plate positions are altered. No metadata output tab is created for this path.

For Plate Template, `plate`, `plate_column` and `plate_coord` must be present and filled for each sample/control. `plate_row`, if present, must agree with plate_coord; otherwise the view derives its row from the coordinate. Wells must be A–H / 1–12; A1 and A01 refer to the same well and cannot both be occupied on the same plate. Plate names may be text, and the same well on different plates is allowed. The same year_collected header is required for both formats, with the four-digit rule. A legacy date_collected column does not substitute for year_collected; dates are not converted automatically. BarcodeSequence is optional in this customer template; its format/uniqueness checks apply if supplied. Recognized control sample types are colored yellow in the view, but this does not certify that the lab's required controls are all present.

Open the source tab and the MetaReady sidebar, then correct highlighted errors. Click **Prepare submission / plate view**. Existing output names are never overwritten. Partly filled or inconsistent plate-position columns cause an error; they never fall back to adding controls. Renaming a plate tab does not bypass detection. The plate view is a snapshot and must be regenerated after changing positions.

## add_controls workflow

Pre-wet-lab and Full metadata are combined in the **add_controls** profile. Old saved `lite` / `full` settings are read as `add_controls`. Validation checks the submission columns, and applies full plate/barcode checks when those columns are present. Assay-specific 16S, ITS and UDI profiles remain available.

1. Open your submitted sample tab, then **Extensions → MetaReady → Check metadata / setup**. Use row 1 for headers. Checking starts automatically for recognized templates.
2. Use `year_collected` instead of `date_collected`. Enter exactly four digits, e.g. `2024`; no range of years is imposed. The old date-format check has been removed from Python and Sheets. Existing dates are not automatically converted to years. `date_collected` may remain as an extra column.
3. In **addControls**, fix source metadata errors. The creation action requires a nonempty SampleID and a four-digit year for every submitted sample. The remaining required source columns are investigator, time_collected, subject_id, host_species and sample_type. Python's existing blank-cell semantics remain for validation; generated controls have no invented collection year or subject information.
4. Select **Shotgun** (including WGS) or **Amplicon** under Plate preparation and click **Prepare submission / plate view**. This is an explicit action, not an automatic edit-trigger action. It uses the merged profile regardless of another selected assay-check profile.
5. After preflight checks succeed, the action first copies the active tab to **metadata_originally_submitted**, preserving formatting and freezing its values. The source tab is left intact. Then it creates **metadata** with the samples and controls, and **plate_review** with an 8 × 12 layout for each plate. Yellow wells identify controls.
6. The metadata tab becomes active and has add_controls validation enabled. The open sidebar automatically installs dropdowns and checks it. Later cell edits automatically update highlights. The plate-review tab is a snapshot; editing metadata does not automatically rearrange the plate view.

The three output names must be unused. If any exists, the operation stops without overwriting it. Rename/archive previous outputs yourself before a new run. If the source itself is named `metadata`, rename it before running. Plate-position columns select the already-plated workflow instead; it requires valid plate_coord and plate_column values. On a write failure, only tabs created by that attempt are rolled back.

## R template behavior

`Controls.gs` ports `plate_review.R`. Default controls per plate:

| Control | Initial well | ID prefix |
| --- | --- | --- |
| Blank swab | G01 | Extractblankswab |
| Empty well | E07 | Extractemptywell |
| DNA-free water | C09 | DNAfreewater |
| Mock DNA | G03 | mockdna |

The planner uses the minimum number of plates at a maximum of 94 submitted samples per plate. It keeps four controls where a plate has at most 92 samples; plates with 93–94 samples receive only DNA-free water and Mock DNA. For example, 94 samples produce one plate with two controls, and 188 samples produce two such plates. Samples fill down A–H, then across columns 01–12. Control IDs use the R numbering (1, 3, 5… by plate) plus the current date in the spreadsheet timezone. Partial plates use the R script's adjustments and gap-compaction algorithm, so final control positions can differ from the table. Specifically, its executable E07→D05 adjustment moves Empty well for a remainder >=32 and <48, despite a source comment referring to DNA-free water. Full 96-well plates retain the initial positions. The original four-control placement was compared against the R script; the adaptive two-control policy is a deliberate extension of that script.

Only output SampleIDs are normalized as in R: trim surrounding whitespace; replace `+`, `-`, `_`, `(` with periods; remove `)`; prefix a digit-starting ID with `s.`. Collisions after normalization or with generated controls stop creation. The original snapshot retains the submitted IDs. Extra source columns are retained; fully blank sample rows are excluded.

R output columns are generated into `Rules.gs` from its Amplicon and Shotgun lists; WGS uses Shotgun columns. Names are aligned with the checker: SampleType→sample_type, date_collected→year_collected, udi_coord→barcode_coord, and column peaks_present→column_peaks_present. SampleType is accepted as an input alias by validation and both preparation paths. Other checker columns use their canonical names. BarcodeSequence is included for full validation; unprovided lab fields remain blank. No barcode sequences or scientific attributes are fabricated.

## Validation and highlighting

Identical errors are grouped per column, with a count. Only the first affected cell per group receives a hover note. Colors are stable by category: duplicates purple, disallowed values orange, whitespace yellow, required values pink, headers blue, formats teal, unavailable vocabularies gray. When the first error is corrected, the note moves to the next affected cell. A cell with several errors shows one category at a time; the sidebar retains all groups.

Highlights are conditional-format overlays. Existing formatting returns when errors clear; unrelated rules are retained. Existing notes before the CHOP marker survive checks. Dropdown validation replaces existing validation on enum columns. The sidebar shows at most 200 groups and is a snapshot until refreshed. Google simple edit triggers have queue/runtime limits and do not run for script/API writes or format-only changes. Always check before sharing. Each project's settings and cached public vocabularies stay in that spreadsheet's document properties.

## Update the Apps Script project

Replace **Code.gs**, **Validator.gs**, **Rules.gs**, and **Sidebar.html**, and add the new script file **Controls.gs**. The manifest is unchanged. Save, execute the **Latest Code** Editor add-on test and reopen the sidebar. No Python or R installation is required for wet lab users; those tools are used only for development.

## Development and verification

From the repository root:

```
python3 google_sheets/generate_rules.py
node google_sheets/test_validator.cjs
node google_sheets/test_controls.cjs
CHOP_R_PARITY=1 node google_sheets/test_controls.cjs
black --check --target-version py313 .
pytest tests
```

R parity tests require Rscript and the template's optparse, tidyverse and reshape2 packages. The remaining JavaScript tests need only Node. The tab adapter tests cover snapshot-first ordering, source preservation, existing-tab refusal and failure rollback. Before publishing, test in real Google Sheets with a disposable submission, partial and full plates, and another project/account. Google authorization and UI behavior cannot be established by local service mocks.

## Small last-plate warning

After successful tube preparation, if the last plate has fewer than 10 occupied wells **including controls**, the sidebar displays a popup and retains this message in its status:

> Please double check number of samples, there is one plate has very few samples after adding controls

Exactly 10 occupied wells does not warn. This is an advisory after output creation, not a blocking validation error. Already-plated submissions do not add controls and do not use this warning. Update Controls.gs and Sidebar.html together to receive the popup.

## Sidebar workflow tabs

The sidebar has two colored main tabs: **addControls** (teal) and **addBarcode** (purple). Existing metadata validation and plate-preparation controls are under addControls. addBarcode contains smaller, individually colored **16SV1V2**, **ITS**, **UDI** and **RNA** subtabs. These are display-only placeholders marked NOT CONFIGURED: selecting them does not run checks, assign barcodes, change a saved profile, or modify spreadsheet data. Barcode behavior will be added when its instructions are supplied. The format selector has been removed. Existing enabled tabs now use automatic format detection, including tabs with legacy saved profiles. The barcode subtabs remain placeholders.

To install this sidebar-only update, replace Sidebar.html in Apps Script and rerun the Latest Code test deployment.

## Automatic format detection in addControls

There is one addControls workflow. The sidebar displays the detected format as text. Checking and preparation use the same detector: any plate, plate_row, plate_column, plate_coord or plate_location_combined column selects the already-plated path, as does the legacy Plate Template tab name. Incomplete or blank plate information fails validation instead of triggering control creation. Without those indicators, tube rules apply. Generated metadata uses plate_location_combined as an alias for plate_coord during validation. Detection is repeated on checks and edit events, not stored as a user choice.

For this update replace Code.gs, Validator.gs and Sidebar.html. Keep Controls.gs installed because it contains the shared detector.

## Automatic current-tab checking (current sidebar)

Load current tab and Enable checking buttons have been removed. Opening addControls in Google Sheets automatically loads missing vocabularies and checks the active tab. While the sidebar is visible on addControls, it polls every five seconds; unchanged displayed data is not rechecked. Switching worksheet tabs or changing data triggers a new check. Manual Check now remains available. Live edit events also update recognized metadata templates without prior per-tab setup. The preserved metadata_originally_submitted tab and generated plate_review/plate_view tabs are excluded from automatic writes. Automatic checks never add controls or generate output tabs; preparation remains an explicit action. First-use Google authorization is still required, and full automatic following only runs while the sidebar is open. Replace Code.gs and Sidebar.html for this update.

Automatic checking requires these exact headers in row 1 (in any order): `SampleID`, `investigator`, `project_name`, `sample_type`, `subject_id`, `host_species`, `study_day`, `study_group`, `current_antibiotics`, `year_collected`, `time_collected`, `mouse_strain`, and `cage_id`. Legacy `SampleType` is accepted for `sample_type`. These are the shared tube/plate template columns; tube-only and plate-only fields do not determine eligibility. A tab containing only SampleID is not enough. Tabs missing any of these headers are left untouched, and the sidebar lists the missing headers. Restoring the headers resumes automatic checking. Header presence is required, but blank values are handled by the validation rules.

## Preserve submission before checking (current workflow)

On the first sidebar check of a recognized template, MetaReady renames the input tab to `metadata_originally_submitted`, copies it to `metadata`, and activates that working copy. Only metadata receives dropdowns, error notes, highlights, corrections and generated controls. The original cells, formatting and formulas are left untouched (formulas remain live). Existing unrelated output names block initialization rather than being overwritten. Later edit checks apply only to the tracked working copy.

Click Shotgun or Amplicon to validate and prepare the working copy. Tube submissions gain controls and positions in metadata plus a plate_review tab. Already-plated submissions retain their existing controls/positions in metadata and gain plate_view. A second preparation is blocked until Reset.

Reset deletes the tracked metadata and generated review tabs (including edits made there), keeps and activates metadata_originally_submitted, and pauses checking. Update that original if needed, then click addControls, Shotgun or Amplicon to create a fresh working copy. It does not create archives or delete unrelated tabs or archives from earlier versions. Tracking remains after a partial deletion failure so Reset can be retried. Barcode Reset only clears its placeholder assay selection.

Replace Code.gs, Controls.gs and Sidebar.html together for this update. This workflow supersedes the earlier preparation-time snapshot instructions above.
