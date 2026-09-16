/** @OnlyCurrentDoc */
function onOpen(e) {
  // Menu-only: safe even before this add-on is authorized in a project sheet.
  SpreadsheetApp.getUi().createAddonMenu()
    .addItem('Check metadata / setup', 'chopSidebar')
    .addItem('Refresh allowed values for this project', 'chopRefreshVocabulary')
    .addToUi();
}

function onInstall(e) { onOpen(e); }

function chopState() {
  const book = SpreadsheetApp.getActive();
  const sheet = book.getActiveSheet();
  const props = PropertiesService.getDocumentProperties();
  return {projectName: book.getName(), sheetName: sheet.getName(), sheetId: sheet.getSheetId(),
    format: chopDetectedProfile_(sheet) === 'plate_template' ? 'Already plated — keep existing controls and positions' : 'Tube format — add controls during preparation',
    profile: props.getProperty('chopProfile_' + sheet.getSheetId()) ? chopDetectedProfile_(sheet) : null};
}

function chopSidebar() {
  SpreadsheetApp.getUi().showSidebar(HtmlService.createHtmlOutputFromFile('Sidebar').setTitle('CHOP Metadata'));
}

function chopRefreshVocabulary() {
  const base = 'https://raw.githubusercontent.com/PennChopMicrobiomeProgram/SampleRegistry/master/sample_registry/data/';
  const vocab = {};
  [['SAMPLE_TYPE_LIST', 'standard_sample_types.tsv', 'sample_type'],
   ['HOST_SPECIES_LIST', 'standard_host_species.tsv', 'host_species']].forEach(item => {
    const response = UrlFetchApp.fetch(base + item[1]);
    const rows = Utilities.parseCsv(response.getContentText(), '\t');
    const col = rows[0].indexOf(item[2]);
    if (col < 0) throw new Error('Vocabulary has no ' + item[2] + ' column. Previous values retained.');
    const values = [...new Set(rows.slice(1).map(r => (r[col] || '').trim()).filter(Boolean))];
    if (!values.length) throw new Error('Empty vocabulary. Previous values retained.');
    vocab[item[0]] = values;
  });
  vocab.HOST_SPECIES_LIST.push(null);
  const props = PropertiesService.getDocumentProperties();
  // Separate properties stay within the per-value size limit; reject oversized lists.
  const data = {};
  Object.keys(vocab).forEach(k => {
    const json = JSON.stringify(vocab[k]);
    if (Utilities.newBlob(json).getBytes().length > 8500) throw new Error('Vocabulary too large for this template; contact the maintainer.');
    data[k] = json;
  });
  data.chopVocabularyUpdated = new Date().toISOString();
  props.setProperties(data);
  SpreadsheetApp.getActive().toast('Allowed values refreshed. Run Check now to update dropdowns.', 'CHOP Metadata');
}

function chopVocab_() {
  const p = PropertiesService.getDocumentProperties();
  return {
    SAMPLE_TYPE_LIST: JSON.parse(p.getProperty('SAMPLE_TYPE_LIST') || '[]'),
    HOST_SPECIES_LIST: JSON.parse(p.getProperty('HOST_SPECIES_LIST') || '[]')
  };
}

function chopConfigure(profile, expectedSheetId) {
  chopRules(profile); // Reject arbitrary profile values.
  const sheet = SpreadsheetApp.getActiveSheet();
  if (sheet.getSheetId() !== Number(expectedSheetId)) throw new Error('The active tab changed. Click Load current tab before choosing its profile.');
  // Document properties are scoped to this add-on AND this spreadsheet, shared
  // by its collaborators; never store project settings in script properties.
  const vocab = chopVocab_();
  if (!vocab.SAMPLE_TYPE_LIST.length || !vocab.HOST_SPECIES_LIST.some(Boolean)) chopRefreshVocabulary();
  PropertiesService.getDocumentProperties().setProperty('chopProfile_' + sheet.getSheetId(), profile);
  return chopCheck();
}

function chopCheck() {
  return chopAutoCheck(null);
}

function chopCheckSheet_(sheet, dropdowns) {
  const props = PropertiesService.getDocumentProperties();

  const profile = chopDetectedProfile_(sheet);
  const range = sheet.getDataRange();
  // Bound the simple trigger workload and never report success for a skipped check.
  if (range.getNumRows() * range.getNumColumns() > 100000) throw new Error('This tab exceeds 100,000 cells. Split the metadata into smaller tabs or use the Python checker.');
  const grid = range.getDisplayValues(), vocab = chopVocab_();
  const result = chopValidate(grid, profile, vocab);
  const groups = chopGroupIssues_(result.issues);
  const previous = JSON.parse(props.getProperty('chopExtent_' + sheet.getSheetId()) || '[1,1]');
  const noteRange = sheet.getRange(1, 1,
    Math.min(sheet.getMaxRows(), Math.max(previous[0], range.getNumRows())),
    Math.min(sheet.getMaxColumns(), Math.max(previous[1], range.getNumColumns())));
  const notes = noteRange.getNotes();
  const marker = '\n[CHOP Metadata]\n';
  notes.forEach(row => row.forEach((note, c) => { row[c] = note.split(marker)[0]; }));
  groups.forEach(group => {
    const first = group.cells[0];
    const explanation = group.message + '\n' + group.count + ' affected cell(s) in this column.' +
      (group.suggestions.length ? '\nSuggested for this first cell: ' + group.suggestions.join(', ') + '. Verify before changing.' : '');
    notes[first.row - 1][first.col - 1] += marker + explanation;
  });
  noteRange.setNotes(notes);
  chopHighlight_(sheet, groups);
  props.setProperty('chopExtent_' + sheet.getSheetId(), JSON.stringify([range.getNumRows(), range.getNumColumns()]));
  if (dropdowns && sheet.getMaxRows() > 1) {
    chopRules(profile).filter(r => r.kind === 'values_in_set').forEach(rule => {
      const c = grid[0].findIndex(h => (h === 'SampleType' ? 'sample_type' : h) === rule.args[0]);
      const list = Array.isArray(rule.args[1]) ? rule.args[1] : vocab[rule.args[1].vocabulary];
      if (c >= 0 && list && list.length) sheet.getRange(2, c + 1, sheet.getMaxRows() - 1, 1)
        .setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(list.filter(v => v !== null), true)
          .setAllowInvalid(true).setHelpText('Choose an allowed value. CHOP Metadata → Check metadata explains errors, including pasted values.').build());
    });
  }
  result.sheetId = sheet.getSheetId();
  result.sheetName = sheet.getName();
  result.checkedAt = new Date().toISOString();
  result.vocabularyUpdated = props.getProperty('chopVocabularyUpdated');
  result.issueCount = result.issues.length;
  result.groupCount = groups.length;
  result.issues = groups.slice(0, 200).map(g => ({
    row: g.cells[0].row, col: g.col, field: g.field, message: g.message,
    suggestions: g.suggestions, count: g.count, color: g.color
  }));
  SpreadsheetApp.getActive().toast(result.passed ? 'Checks passed for ' + profile + '. Recheck before sharing.' : result.groupCount + ' error groups. Hover over the first highlighted cell in each column.', 'CHOP Metadata', 8);
  return result;
}

function onEdit(e) {
  if (!e || !e.range) return;
  if (e.authMode === ScriptApp.AuthMode.NONE) return;
  const sheet = e.range.getSheet();
  if (chopSkipAuto_(sheet)) return;

  const lock = LockService.getDocumentLock();
  if (!lock.tryLock(1000)) {
    e.source.toast('Another check is running. Use Check now before sharing.', 'CHOP Metadata');
    return;
  }
  try {
    const workspace=JSON.parse(PropertiesService.getDocumentProperties().getProperty('chopWorkspace')||'null');
    if(workspace&&workspace.workingId===sheet.getSheetId())chopCheckSheet_(sheet,false);
  }
  catch (error) { e.source.toast('Check incomplete: ' + error.message, 'CHOP Metadata', 10); }
  finally { lock.releaseLock(); }
}

function chopGoTo(sheetId, row, col) {
  const sheet = SpreadsheetApp.getActive().getSheets().find(s => s.getSheetId() === Number(sheetId));
  if (!sheet) throw new Error('The metadata tab was deleted. Run Check now again.');
  sheet.activate();
  sheet.getRange(Number(row), Number(col)).activate();
}

// Stable categories keep colors unchanged when other errors are corrected.
function chopErrorType_(message) {
  if (message.startsWith('Duplicate ')) return 'duplicate';
  if (message.startsWith('Choose an allowed')) return 'allowed';
  if (message.startsWith('Remove spaces')) return 'whitespace';
  if (message.startsWith('Fill in ') || message === 'This value is required.') return 'required';
  if (message.startsWith('Allowed values unavailable')) return 'unavailable';
  if (/header|column name|Missing required column|Headers may|Enter at least/.test(message)) return 'header';
  return 'format';
}

function chopGroupIssues_(issues) {
  const colors = {duplicate:'#e4d7f5', allowed:'#fce4c5', whitespace:'#fff2b3',
    required:'#f8cdd3', unavailable:'#d9d9d9', header:'#cde5fa', format:'#c9ece6'};
  const groups = new Map();
  issues.forEach(i => {
    const type = chopErrorType_(i.message);
    // Duplicate row numbers vary by duplicated value; combine them in a column.
    const message = type === 'duplicate' ? i.message.replace(/ in rows .*?\. Verify/, '. Verify') : i.message;
    const key = JSON.stringify([i.col, message]);
    if (!groups.has(key)) groups.set(key, {col:i.col, field:i.field, message,
      color:colors[type], type, cells:[], suggestions:[]});
    const g = groups.get(key);
    if (!g.cells.some(c => c.row === i.row)) g.cells.push(i);
  });
  return [...groups.values()].map(g => {
    g.cells.sort((a,b) => a.row - b.row);
    g.count = g.cells.length;
    g.suggestions = g.cells[0].suggestions;
    return g;
  });
}

function chopHighlight_(sheet, groups) {
  const marker = 'CHOP_METADATA_HIGHLIGHT:';
  const existing = sheet.getConditionalFormatRules().filter(rule => {
    const condition = rule.getBooleanCondition();
    return !condition || !condition.getCriteriaValues().some(v => String(v).includes(marker));
  });
  const byColor = new Map();
  // One cell has one background. If several errors apply, show the first rule's
  // category until fixed; notes/sidebar still include all of that cell's issues.
  const assigned = new Set();
  groups.forEach(g => g.cells.forEach(cell => {
    const key = cell.row + ',' + cell.col;
    if (assigned.has(key)) return;
    assigned.add(key);
    if (!byColor.has(g.color)) byColor.set(g.color, []);
    byColor.get(g.color).push(cell);
  }));
  const rules = [];
  byColor.forEach((cells, color) => {
    cells.sort((a,b) => a.col - b.col || a.row - b.row);
    const spans = [];
    cells.forEach(cell => {
      const last = spans[spans.length - 1];
      if (last && last.col === cell.col && last.end + 1 === cell.row) last.end = cell.row;
      else spans.push({col:cell.col, row:cell.row, end:cell.row});
    });
    const ranges = spans.map(s => sheet.getRange(s.row, s.col, s.end - s.row + 1, 1));
    rules.push(SpreadsheetApp.newConditionalFormatRule()
      .whenFormulaSatisfied('=N("' + marker + color + '")=0')
      .setBackground(color).setRanges(ranges).build());
  });
  // Removing our overlay reveals the original cell background/formatting.
  sheet.setConditionalFormatRules(rules.concat(existing));
}

function chopProfile_(profile) {
  return profile === 'lite' || profile === 'full' ? 'add_controls' : profile;
}

function chopDetectedProfile_(sheet) {
  const state=JSON.parse(PropertiesService.getDocumentProperties().getProperty('chopWorkspace')||'null');
  if(state&&state.workingId===sheet.getSheetId()&&state.alreadyPlated)return 'plate_template';
  return chopIsPlateSubmission_(sheet.getDataRange().getDisplayValues(), sheet.getName()) ? 'plate_template' : 'add_controls';
}

function chopSkipAuto_(sheet) {
  return chopAutoSkipReason_(sheet) !== '';
}

// Called by the open sidebar. No setup click is needed; reads never add controls.
function chopAutoCheck(previousToken, restart) {
  const book=SpreadsheetApp.getActive();
  let sheet=book.getActiveSheet();
  const props=PropertiesService.getDocumentProperties();
  const workspace=JSON.parse(props.getProperty('chopWorkspace')||'null');
  let missingWorking=false;
  if(workspace&&workspace.sourceId===sheet.getSheetId()&&workspace.workingId!==null){
    const working=book.getSheets().find(s=>s.getSheetId()===workspace.workingId);
    if(working){working.activate();sheet=working;}
    else missingWorking=true;
  }
  const resuming=missingWorking||(restart&&workspace&&workspace.workingId===null&&workspace.sourceId===sheet.getSheetId())||(!workspace&&sheet.getName()==='metadata_originally_submitted');
  const skipReason=chopAutoSkipReason_(sheet, resuming), skipped=!!skipReason;
  const range=sheet.getDataRange();
  if(!skipped && range.getNumRows()*range.getNumColumns()>100000) throw new Error('This tab exceeds 100,000 cells.');
  const payload=JSON.stringify([sheet.getSheetId(),sheet.getName(),skipReason,skipped?null:range.getDisplayValues(),props.getProperty('chopVocabularyUpdated')]);
  const token=Utilities.base64Encode(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,payload));
  if(token===previousToken)return null;
  if(skipped)return {token,skipped:true,skipReason,sheetId:sheet.getSheetId(),sheetName:sheet.getName(),projectName:book.getName()};
  const lock=LockService.getDocumentLock();
  if(!lock.tryLock(1000))return null;
  try {
    const working=chopEnsureWorkspace_(book,sheet);
    const vocab=chopVocab_();
    if(!vocab.SAMPLE_TYPE_LIST.length||!vocab.HOST_SPECIES_LIST.some(Boolean))chopRefreshVocabulary();
    const result=chopCheckSheet_(working,true);
    result.token=working.getSheetId()===sheet.getSheetId()?token:null;result.projectName=book.getName();return result;
  } finally {lock.releaseLock();}
}

function chopAutoSkipReason_(sheet, resuming) {
  const workspace=JSON.parse(PropertiesService.getDocumentProperties().getProperty('chopWorkspace')||'null');
  if(!resuming&&workspace&&workspace.sourceId===sheet.getSheetId())return 'Preserved original submission. Make corrections in metadata.';
  if (sheet.getName().startsWith('MetaReady_archive_')) return 'Archived preparation output. Select your current metadata input tab.';
  if (!resuming&&['metadata_originally_submitted','plate_review','plate_view'].includes(sheet.getName()))
    return 'This is a preserved submission or plate-view output. Select a metadata input tab.';
  // Once recognized, missing/edited headers are validation errors on the working copy.
  if(workspace&&workspace.workingId===sheet.getSheetId())return '';
  const required=['SampleID','investigator','project_name','sample_type','subject_id','host_species',
    'study_day','study_group','current_antibiotics','year_collected','time_collected','mouse_strain','cage_id'];
  const headers=sheet.getRange(1,1,1,Math.max(1,sheet.getLastColumn())).getDisplayValues()[0]
    .map(h=>h==='SampleType'?'sample_type':h);
  const missing=required.filter(h=>!headers.includes(h));
  return missing.length ? 'Not a metadata template: missing header(s) '+missing.join(', ')+'. This tab has not been checked or changed.' : '';
}
