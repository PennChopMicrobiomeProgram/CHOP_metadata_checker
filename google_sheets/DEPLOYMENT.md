# Deploy the CHOP Metadata Editor add-on

## Create the central project

1. In your organization's Google account, create a **standalone** project at [Apps Script](https://script.google.com/home). Name it **CHOP Metadata**. Do not create it through an individual spreadsheet's Extensions → Apps Script command.
2. Add `Code.gs`, `Rules.gs`, `Validator.gs`, `Controls.gs`, and an HTML file named `Sidebar` containing `Sidebar.html`. These are the only code files to upload; exclude tests, Python and documentation.
3. In Project Settings, show the manifest and replace `appsscript.json` with the supplied file. Its scopes cover the current spreadsheet, the sidebar, and outbound requests for public vocabularies. It does not request Drive-wide access. This is an **Editor add-on**, using HTML Service and `createAddonMenu`, so no card-based `addOns` manifest section is needed.
4. Choose an organizational maintainer and retain access to this standalone project. Project metadata remains in the individual Sheets, not in the central Apps Script project. The add-on stores profiles, note-range extents and vocabulary caches in document properties; metadata is read to check and annotate the current sheet and is not sent to an external validation service.

## Test before publication

1. Prepare two disposable Google Sheets representing separate projects. Give them different checking profiles, even if they have identically named tabs.
2. In Apps Script choose **Deploy → Test deployments → Select type → Editor add-on → Create new test**. Select **Latest Code**, an authorization state, and one test spreadsheet. Save, then select the saved test and **Execute**. Repeat for the other spreadsheet.
3. Test both **Installed for current user** (`AuthMode.NONE`) and enabled states. The menu must appear before authorization without accessing document properties or fetching data. Open the sidebar from the menu to authorize. Do not run `onEdit` manually from the script editor.
4. Enable a tab, verify automatic vocabulary loading and dropdowns, then paste bad values, duplicate IDs/plate positions, whitespace and missing dependent fields. Verify cell notes and the sidebar links; correct the entries and recheck. Ensure existing lab notes survive.
5. Switch between the two projects and reopen the sidebar: each must retain its own profile. Change tabs while the sidebar is open: **Load current tab** updates setup, and an attempted setup using the previous tab must be rejected. **Check now** checks the current active tab and labels the result accordingly.
6. Test with another editor, including the installation/authorization prompt. Test unavailable vocabulary fetches: setup must report failure rather than certify a sheet. Test read-only access and script/API edits: manual validation with edit access remains necessary before sharing.

This implementation uses simple `onOpen`, `onInstall` and `onEdit` triggers, not per-project installable triggers. Automatic edit checks apply when the add-on is enabled and Google delivers the edit event; they are not guaranteed background monitoring. Simple trigger quotas and queue limits still apply. The local Node tests use service doubles and cannot establish live Google authorization/UI behavior.

## Publish privately for the center

1. Associate the standalone Apps Script project with a **standard Google Cloud project** controlled by your organization.
2. Configure the Google Auth consent screen for the intended organizational audience and the exact three scopes from `appsscript.json`.
3. Enable and configure the **Google Workspace Marketplace SDK** in that Cloud project. Select **Editor add-on / Sheets**, and supply the Apps Script project ID and an immutable script **version number** for the tested release (not a Workspace card add-on deployment ID).
4. Choose **Private** visibility for your Google Workspace organization when available. Confirm the organization with your administrator before selecting visibility. Private availability is domain-scoped; collaborators outside that organization require a separately planned distribution path.
5. Complete the Marketplace listing using your organization's real support contact, icons/screenshots and required policy URLs. Describe the app as validating the currently open metadata sheet, adding error notes and dropdowns, with no automatic metadata value changes during validation; the explicit add_controls action copies the submission and creates metadata and plate-review tabs. Do not claim Google or CHOP approval that has not been obtained.
6. Publish after the live tests pass. Have the Workspace administrator allow or distribute the add-on to the intended users, or provide its private Marketplace installation link. Publication and admin configuration require the organization's account; no publication has been performed by the local build.

## Existing projects and updates

Each user installs once (or receives the administrator's deployment), then uses the same add-on in every authorized project sheet. A project coordinator enables the appropriate metadata tabs once per project. Existing shared URLs remain unchanged.

If a project already has the earlier bound checker installed, remove only its old checker files/triggers after verifying the central add-on in a copy; preserve unrelated bound scripts. Otherwise both checkers may run and overwrite each other's CHOP notes. The new add-on cannot read the old script's document properties, so enable its profiles again. It can replace old CHOP note sections on the next check.

For updates, regenerate `Rules.gs` if Python rules changed, run local and live tests, create a new script version, and update the Marketplace SDK's Editor add-on version. Users then receive the centrally published code without copying scripts into each sheet. Keep the previous release version available for rollback.

Sources: [Build Editor add-ons](https://developers.google.com/workspace/add-ons/how-tos/building-editor-addons), [test deployments](https://developers.google.com/workspace/add-ons/how-tos/testing-editor-addons), [authorization lifecycle](https://developers.google.com/workspace/add-ons/concepts/editor-auth-lifecycle), [publication](https://developers.google.com/workspace/add-ons/how-tos/publish-add-on-overview).

For the add_controls release, use a source tab without plate-position columns and four-digit year_collected values. Test creation of metadata_originally_submitted, metadata and plate_review, control locations, repeat-run refusal and preservation of the original source. See README.md for the full workflow.

Test the customer Plate Template separately: include year_collected, sample_type and populated plate/plate_column/plate_coord columns. Verify only the preserved submission and plate_view are created, IDs/positions remain identical, no controls are added, and duplicate or contradictory wells block creation. Test Tube_format to ensure its control-generation workflow remains unchanged.
