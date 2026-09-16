/* Plate preparation ported from plate_review.R. No Google services in the planner. */
function chopPlanControls_(grid, runType, stamp, vocab) {
  if (runType === 'WGS') runType = 'Shotgun'; // Compatibility with older sidebar versions.
  if (!['Amplicon', 'Shotgun'].includes(runType)) throw new Error('Choose Amplicon or Shotgun.');
  if (!/^\d{8}$/.test(stamp)) throw new Error('Control ID date must be YYYYMMDD.');
  let headers = (grid[0] || []).map(String);
  if (new Set(headers).size !== headers.length || headers.some(h => !h)) throw new Error('Fix empty or duplicate column headers first.');
  if (headers.some(h => ['plate','plate_row','plate_column','plate_location_combined'].includes(h)))
    throw new Error('Use the original sample submission without plate-position columns. Controls must not be added to an already laid-out plate.');
  const aliases = {SampleType:'sample_type', udi_coord:'barcode_coord', 'column peaks_present':'column_peaks_present'};
  headers = headers.map(h => aliases[h] || h);
  if (new Set(headers).size !== headers.length) throw new Error('Both an old and new column name exist (for example SampleType and sample_type). Resolve them first.');
  if (!headers.includes('year_collected')) throw new Error('Add year_collected with four-digit years. Dates are not converted automatically; date_collected can remain as an extra column.');
  const missing = v => v == null || ['', 'NA', 'N/A', 'na', 'n/a', 'Null', 'null', 'None', 'none', '0000-00-00'].includes(String(v));
  const source = grid.slice(1).filter(row => row.some(v => !missing(v))).map(row => headers.map((_,c) => missing(row[c]) ? '' : String(row[c])));
  if (!source.length) throw new Error('No samples to place.');
  const idCol = headers.indexOf('SampleID'), yearCol = headers.indexOf('year_collected');
  if (idCol < 0) throw new Error('SampleID is required.');
  const changes = [];
  source.forEach((row,i) => {
    const original = row[idCol];
    let id = original.trim().replace(/[+_\-(]/g,'.').replace(/\)/g,'');
    if (/^[0-9]/.test(id)) id = 's.' + id;
    if (!id) throw new Error('A sample has an empty SampleID.');
    if (!/^[0-9]{4}$/.test(row[yearCol])) throw new Error('Sample ' + original + ': year_collected must contain exactly four digits.');
    if (id !== original) changes.push({original, updated:id});
    row[idCol] = id;
  });
  if (new Set(source.map(r => r[idCol])).size !== source.length) throw new Error('SampleIDs are duplicated after the R template’s ID cleanup. Fix the submission before adding controls.');
  const checked = chopValidate([headers].concat(source), 'add_controls', vocab);
  if (!checked.passed) throw new Error('Fix the submission before adding controls: ' + checked.issues.slice(0,5).map(i => i.field + ': ' + i.message).join(' | '));
  const definitions = [
    {well:'G01', prefix:'Extractblankswab', type:'Blank swab'},
    {well:'E07', prefix:'Extractemptywell', type:'Empty well'},
    {well:'C09', prefix:'DNAfreewater', type:'DNA-free water'},
    {well:'G03', prefix:'mockdna', type:'Mock DNA'}
  ];
  const plateCount = Math.ceil(source.length / 94), counts = [];
  let remaining = source.length;
  for (let i = 0; i < plateCount; i++) {
    const count = Math.min(94, Math.max(Math.min(92, remaining), remaining - 94 * (plateCount - i - 1)));
    counts.push(count); remaining -= count;
  }
  const controlsPerPlate = counts.map(n => n > 92 ? 2 : 4);
  const controlCount = controlsPerPlate.reduce((a,b) => a+b,0);
  definitions.filter(d => controlsPerPlate.includes(4) || ['DNAfreewater','mockdna'].includes(d.prefix)).forEach(d => {
    if (!vocab.SAMPLE_TYPE_LIST.includes(d.type)) throw new Error('Control sample_type is missing from allowed values: ' + d.type);
  });
  const wells = [], ids = new Set(source.map(r => r[idCol]));
  for (let plate = 1; plate <= plateCount; plate++) {
    for (let col = 1; col <= 12; col++) for (const row of 'ABCDEFGH') {
      const column = String(col).padStart(2,'0'), position = row + column;
      const control = definitions.find(d => d.well === position && (controlsPerPlate[plate-1] === 4 || ['DNAfreewater','mockdna'].includes(d.prefix)));
      const record = control ? {SampleID:control.prefix + (1 + (plate - 1) * 2) + '.' + stamp, sample_type:control.type} : null;
      if (record && ids.has(record.SampleID)) throw new Error('A submitted SampleID conflicts with a generated control: ' + record.SampleID);
      if (record) ids.add(record.SampleID);
      wells.push({plate:String(plate), plate_row:row, plate_column:column, plate_location_combined:position, record, control:!!control});
    }
  }
  // Preserve executable R behavior: this moves Empty well, despite the R comment
  // naming DNA-free water. The range is >=32 and <48 after prior-plate controls.
  const remainder = counts[plateCount - 1];
  if (remainder >= 32 && remainder < 48) {
    const from = wells.find(w => w.plate === String(plateCount) && w.plate_location_combined === 'E07');
    const to = wells.find(w => w.plate === String(plateCount) && w.plate_location_combined === 'D05');
    to.record = from.record; to.control = true; from.record = null; from.control = false;
  }
  let cursor = 0;
  const placed = counts.map(() => 0);
  wells.forEach(w => {
    if (!w.record && placed[Number(w.plate)-1] < counts[Number(w.plate)-1]) {
      placed[Number(w.plate)-1]++;
      const row = source[cursor++];
      w.record = Object.fromEntries(headers.map((h,c) => [h,row[c]]));
    }
  });
  const firstBlank = wells.findIndex(w => w.plate === String(plateCount) && !w.record);
  if (firstBlank !== -1) {
    const nonBlank = wells.map((w,i) => w.plate === String(plateCount) && w.record ? i : -1).filter(i => i !== -1);
    let move = nonBlank.filter(i => i > firstBlank);
    const intervals = nonBlank.filter((index,i) => i < nonBlank.length - 1 && nonBlank[i+1] - index > 1);
    if (intervals.length > 1 && intervals[1] - intervals[0] <= move.length) move = move.slice(1);
    const records = move.map(i => ({record:wells[i].record, control:wells[i].control}));
    move.forEach(i => { wells[i].record = null; wells[i].control = false; });
    const blanks = wells.map((w,i) => w.plate === String(plateCount) && !w.record ? i : -1).filter(i => i !== -1);
    records.forEach((record,i) => Object.assign(wells[blanks[i]], record));
  }
  const outputHeaders = [...new Set(headers.concat(['plate','plate_row','plate_column','plate_location_combined','BarcodeSequence'], CHOP_PLATE_COLUMNS[runType]))];
  const occupied = wells.filter(w => w.record);
  if (cursor !== source.length || occupied.length !== source.length + controlCount) throw new Error('Plate count verification failed. No output written.');
  const metadata = [outputHeaders].concat(occupied.map(w => outputHeaders.map(h => ['plate','plate_row','plate_column','plate_location_combined'].includes(h) ? w[h] : (w.record[h] || ''))));
  const review = [], colors = [];
  for (let plate = 1; plate <= plateCount; plate++) {
    review.push(['plate' + plate].concat(Array.from({length:12},(_,i) => String(i+1).padStart(2,'0'))));
    colors.push(Array(13).fill('#cde5fa'));
    for (const row of 'ABCDEFGH') {
      const line = [row], paint = ['#cde5fa'];
      for (let col = 1; col <= 12; col++) {
        const w = wells[(plate-1)*96 + (col-1)*8 + 'ABCDEFGH'.indexOf(row)];
        line.push(w.record ? w.record.SampleID : '');
        paint.push(w.control ? '#fff2b3' : '#ffffff');
      }
      review.push(line); colors.push(paint);
    }
    review.push(Array(13).fill('')); colors.push(Array(13).fill('#ffffff'));
  }
  const lastPlateOccupancy = counts[plateCount-1] + controlsPerPlate[plateCount-1];
  const warning = lastPlateOccupancy < 10 ? 'Please double check number of samples, there is one plate has very few samples after adding controls' : '';
  return {metadata, review, colors, plateCount, sampleCount:source.length, controlCount, changes, lastPlateOccupancy, warning};
}

function chopAddControls(runType, expectedSheetId) {
  if(PropertiesService.getDocumentProperties().getProperty('chopWorkspace'))return chopPrepareWorkspace_(runType,expectedSheetId);
  const book = SpreadsheetApp.getActive(), source = book.getActiveSheet();
  if (source.getSheetId() !== Number(expectedSheetId)) throw new Error('The active tab changed. Load current tab again.');
  if (chopIsPlateSubmission_(source.getDataRange().getDisplayValues(),source.getName())) return chopReviewSubmittedPlate_(book,source);
  const lock = LockService.getDocumentLock();
  if (!lock.tryLock(1000)) throw new Error('Another operation is running. Try again shortly.');
  const created = [];
  try {
    const names = ['metadata_originally_submitted','metadata','plate_review'];
    if (names.some(name => book.getSheetByName(name))) throw new Error('Output tab names already exist. Rename the existing metadata_originally_submitted, metadata or plate_review tabs before running. Existing tabs are never overwritten.');
    const data = source.getDataRange();
    if (data.getNumRows() * data.getNumColumns() > 100000) throw new Error('Submission exceeds 100,000 cells.');
    let vocab = chopVocab_();
    if (!vocab.SAMPLE_TYPE_LIST.length || !vocab.HOST_SPECIES_LIST.some(Boolean)) { chopRefreshVocabulary(); vocab = chopVocab_(); }
    const plan = chopPlanControls_(data.getDisplayValues(), runType, Utilities.formatDate(new Date(), book.getSpreadsheetTimeZone(), 'yyyyMMdd'), vocab);
    if (plan.metadata.length * plan.metadata[0].length > 100000) throw new Error('Generated metadata exceeds the 100,000-cell validation limit. Split the project before adding controls.');
    // First output is a copy with values frozen to the submitted snapshot.
    const backup = source.copyTo(book); created.push(backup); backup.setName(names[0]);
    data.copyTo(backup.getRange(1,1,data.getNumRows(),data.getNumColumns()), SpreadsheetApp.CopyPasteType.PASTE_VALUES, false);
    const metadata = book.insertSheet(names[1]); created.push(metadata);
    const review = book.insertSheet(names[2]); created.push(review);
    chopWriteTable_(metadata, plan.metadata);
    chopWriteTable_(review, plan.review);
    review.getRange(1,1,plan.colors.length,13).setBackgrounds(plan.colors);
    review.setColumnWidth(1,75); review.setColumnWidths(2,12,150);
    review.getDataRange().setWrap(true);
    review.getRange('A1').setNote('Generated plate layout. Yellow wells are controls. This is a snapshot; changes in metadata do not regenerate it.');
    metadata.getRange(1,1,1,plan.metadata[0].length).setBackground('#cde5fa').setFontWeight('bold');
    metadata.setColumnWidths(1,plan.metadata[0].length,140);
    PropertiesService.getDocumentProperties().setProperty('chopProfile_' + metadata.getSheetId(), 'add_controls');
    metadata.activate();
    chopRememberPreparation_(source, created);
    return {sampleCount:plan.sampleCount, controlCount:plan.controlCount, plateCount:plan.plateCount, changedIds:plan.changes.length, warning:plan.warning, lastPlateOccupancy:plan.lastPlateOccupancy};
  } catch (error) {
    // Roll back only tabs created by this invocation; never touch existing tabs.
    const failures = [];
    created.reverse().forEach(sheet => { try { book.deleteSheet(sheet); } catch (_) { failures.push(sheet.getName()); } });
    throw new Error(error.message + (failures.length ? ' Could not remove partial output tabs: ' + failures.join(', ') : ''));
  } finally { lock.releaseLock(); }
}

function chopWriteTable_(sheet, table) {
  if (sheet.getMaxRows() < table.length) sheet.insertRowsAfter(sheet.getMaxRows(), table.length - sheet.getMaxRows());
  if (sheet.getMaxColumns() < table[0].length) sheet.insertColumnsAfter(sheet.getMaxColumns(), table[0].length - sheet.getMaxColumns());
  // Plain text preserves leading-zero well columns and prevents formula execution.
  const safe = table.map(row => row.map(v => String(v).startsWith('=') || String(v).startsWith("'") ? "'" + v : v));
  sheet.getRange(1,1,table.length,table[0].length).setNumberFormat('@').setValues(safe);
  sheet.setFrozenRows(1);
}

function chopIsPlateSubmission_(grid,name) {
  return name === 'Plate Template' || (grid[0]||[]).some(h=>['plate','plate_row','plate_column','plate_coord','plate_location_combined'].includes(h));
}

function chopPlanSubmittedPlate_(grid,vocab) {
  const checked=chopValidate(grid,'plate_template',vocab);
  if(!checked.passed) throw new Error('Fix the plate submission before creating plate_view: '+checked.issues.slice(0,5).map(i=>'Row '+i.row+' '+i.field+': '+i.message).join(' | '));
  const positions=chopPlatePositions_(grid).placements;
  const plates=[...new Set(positions.map(p=>p.plate))], review=[], colors=[];
  const controls=new Set(['Blank swab','Empty well','DNA-free water','Mock DNA']);
  const byWell=new Map(positions.map(p=>[JSON.stringify([p.plate,p.row,p.column]),p]));
  plates.forEach(plate=>{
    review.push([plate].concat(Array.from({length:12},(_,i)=>String(i+1).padStart(2,'0'))));colors.push(Array(13).fill('#cde5fa'));
    for(const row of 'ABCDEFGH') {
      const line=[row], paint=['#cde5fa'];
      for(let col=1;col<=12;col++) {
        const p=byWell.get(JSON.stringify([plate,row,col]));
        line.push(p?p.id:'');paint.push(p&&controls.has(p.type)?'#fff2b3':'#ffffff');
      }
      review.push(line);colors.push(paint);
    }
    review.push(Array(13).fill(''));colors.push(Array(13).fill('#ffffff'));
  });
  return {review,colors,plateCount:plates.length,sampleCount:positions.length};
}

function chopReviewSubmittedPlate_(book,source) {
  const lock=LockService.getDocumentLock();
  if(!lock.tryLock(1000))throw new Error('Another operation is running. Try again shortly.');
  const created=[];
  try {
    if(book.getSheetByName('metadata_originally_submitted')||book.getSheetByName('plate_view'))
      throw new Error('metadata_originally_submitted or plate_view already exists. Existing tabs are never overwritten.');
    const data=source.getDataRange();
    if(data.getNumRows()*data.getNumColumns()>100000)throw new Error('Submission exceeds 100,000 cells.');
    let vocab=chopVocab_();
    if(!vocab.SAMPLE_TYPE_LIST.length||!vocab.HOST_SPECIES_LIST.some(Boolean)){chopRefreshVocabulary();vocab=chopVocab_();}
    const plan=chopPlanSubmittedPlate_(data.getDisplayValues(),vocab);
    const backup=source.copyTo(book);created.push(backup);backup.setName('metadata_originally_submitted');
    data.copyTo(backup.getRange(1,1,data.getNumRows(),data.getNumColumns()),SpreadsheetApp.CopyPasteType.PASTE_VALUES,false);
    const review=book.insertSheet('plate_view');created.push(review);
    chopWriteTable_(review,plan.review);
    review.getRange(1,1,plan.colors.length,13).setBackgrounds(plan.colors);
    review.setColumnWidth(1,110);review.setColumnWidths(2,12,150);review.getDataRange().setWrap(true);
    review.getRange('A1').setNote('Submitted plate positions, unchanged. Yellow indicates a recognized control sample type. No controls were added or moved. Snapshot; regenerate after metadata changes.');
    PropertiesService.getDocumentProperties().setProperty('chopProfile_'+source.getSheetId(),'plate_template');
    review.activate();
    chopRememberPreparation_(source, created);
    return {alreadyPlated:true,sampleCount:plan.sampleCount,plateCount:plan.plateCount,controlCount:0,changedIds:0};
  } catch(error) {
    const failures=[];
    created.reverse().forEach(s=>{try{book.deleteSheet(s);}catch(_){failures.push(s.getName());}});
    throw new Error(error.message+(failures.length?' Partial tabs could not be removed: '+failures.join(', '):''));
  } finally {lock.releaseLock();}
}

// Track identities rather than names so reset never archives an unrelated tab.
function chopRememberPreparation_(source, outputs) {
  PropertiesService.getDocumentProperties().setProperty('chopPreparation', JSON.stringify({
    sourceId: source.getSheetId(), outputIds: outputs.map(s => s.getSheetId())
  }));
}

function chopResetControls() {
  const lock=LockService.getDocumentLock();
  if(!lock.tryLock(1000))throw new Error('Another operation is running. Try again shortly.');
  try{
    const book=SpreadsheetApp.getActive(),props=PropertiesService.getDocumentProperties(),sheets=book.getSheets();
    let state=JSON.parse(props.getProperty('chopWorkspace')||'null');
    const legacy=JSON.parse(props.getProperty('chopPreparation')||'null');
    if(!state&&!legacy)return {message:'No tracked preparation to reset. Older untracked outputs must be removed manually.',paused:true};
    if(!state){
      const original=sheets.find(s=>legacy.outputIds.includes(s.getSheetId())&&s.getName()==='metadata_originally_submitted');
      if(!original)throw new Error('The preserved original submission is missing. No tabs were deleted.');
      state={sourceId:original.getSheetId(),workingId:null,reviewIds:legacy.outputIds.filter(id=>id!==original.getSheetId()),originalName:'metadata_originally_submitted',alreadyPlated:chopIsPlateSubmission_(original.getDataRange().getDisplayValues(),''),prepared:true};
    }
    const original=sheets.find(s=>s.getSheetId()===state.sourceId);
    if(!original)throw new Error('The original input tab is missing. No tabs were deleted.');
    const conflict=book.getSheetByName('metadata_originally_submitted');
    if(conflict&&conflict.getSheetId()!==original.getSheetId())throw new Error('Another tab has the preserved submission name. No tabs were deleted.');
    original.setName('metadata_originally_submitted');original.activate();
    // Keep tracking until all deletions succeed so a partial failure can be retried.
    props.setProperty('chopWorkspace',JSON.stringify(state));
    const ids=[state.workingId].concat(state.reviewIds||[]);
    for(const id of ids){
      const sheet=sheets.find(s=>s.getSheetId()===id);
      if(sheet&&id!==state.sourceId)book.deleteSheet(sheet);
    }
    state.workingId=null;state.reviewIds=[];state.prepared=false;
    props.setProperty('chopWorkspace',JSON.stringify(state));
    props.deleteProperty('chopPreparation');
    return {message:'Reset complete. Generated tabs were deleted. metadata_originally_submitted is preserved. Update it if needed, then click Shotgun or Amplicon to create a fresh metadata copy.',sourceId:state.sourceId,paused:true};
  }finally{lock.releaseLock();}
}

// Called under the document lock, before validation can change the input.
function chopEnsureWorkspace_(book, source) {
  const props=PropertiesService.getDocumentProperties();
  let saved=JSON.parse(props.getProperty('chopWorkspace')||'null');
  if(saved&&saved.workingId!==null&&source.getSheetId()===saved.sourceId&&!book.getSheets().some(s=>s.getSheetId()===saved.workingId)){
    const reviews=saved.reviewIds||[];
    if(book.getSheets().some(s=>reviews.includes(s.getSheetId()))||book.getSheetByName('plate_review')||book.getSheetByName('plate_view'))
      throw new Error('The working metadata tab was deleted, but a previous plate view remains. Click Reset to remove that generated output before restarting.');
    saved={...saved,workingId:null,prepared:false,reviewIds:[]};
  }
  if(saved&&saved.workingId!==null){
    if(source.getSheetId()!==saved.workingId) throw new Error('A submission is already open. Use metadata, or Reset before starting another submission.');
    return source;
  }
  if(saved&&source.getSheetId()!==saved.sourceId)throw new Error('Select metadata_originally_submitted to restart.');
  if((book.getSheetByName('metadata_originally_submitted')&&book.getSheetByName('metadata_originally_submitted').getSheetId()!==source.getSheetId()) || (book.getSheetByName('metadata') && source.getName()!=='metadata'))
    throw new Error('Existing metadata tabs belong to an earlier submission. Reset or archive them before checking this input.');
  const originalName=source.getName();
  let working;
  try {
    working=source.copyTo(book);
    source.setName('metadata_originally_submitted');
    working.setName('metadata');
    // Freeze the working values; leave every original cell and formula untouched.
    const data=source.getDataRange();
    data.copyTo(working.getRange(1,1,data.getNumRows(),data.getNumColumns()),SpreadsheetApp.CopyPasteType.PASTE_VALUES,false);
    working.activate();
    props.setProperty('chopWorkspace',JSON.stringify({sourceId:source.getSheetId(),workingId:working.getSheetId(),originalName,alreadyPlated:(saved&&saved.alreadyPlated)||chopIsPlateSubmission_(data.getDisplayValues(),originalName),reviewIds:[],prepared:false}));
    return working;
  } catch(error){
    if(working)book.deleteSheet(working);
    source.setName(originalName);
    throw error;
  }
}

function chopPrepareWorkspace_(runType,expectedSheetId){
  const lock=LockService.getDocumentLock();
  if(!lock.tryLock(1000))throw new Error('Another operation is running. Try again shortly.');
  let recovery,review,source,previousState;
  let wrote=false;
  try{
    const book=SpreadsheetApp.getActive(),props=PropertiesService.getDocumentProperties();
    previousState=props.getProperty('chopWorkspace');
    const state=JSON.parse(previousState);
    source=book.getActiveSheet();
    if(source.getSheetId()!==Number(expectedSheetId)||source.getSheetId()!==state.workingId)throw new Error('Select the metadata working tab before preparing.');
    if(state.prepared)throw new Error('This submission is already prepared. Use Reset before preparing again.');
    const alreadyPlated=state.alreadyPlated||chopIsPlateSubmission_(source.getDataRange().getDisplayValues(),source.getName());
    const name=alreadyPlated?'plate_view':'plate_review';
    if(book.getSheetByName(name))throw new Error(name+' already exists. Reset or archive it first.');
    const data=source.getDataRange();
    if(data.getNumRows()*data.getNumColumns()>100000)throw new Error('Submission exceeds 100,000 cells.');
    const vocab=chopVocab_();
    const plan=alreadyPlated?chopPlanSubmittedPlate_(data.getDisplayValues(),vocab):chopPlanControls_(data.getDisplayValues(),runType,Utilities.formatDate(new Date(),book.getSpreadsheetTimeZone(),'yyyyMMdd'),vocab);
    if(plan.metadata&&plan.metadata.length*plan.metadata[0].length>100000)throw new Error('Generated metadata exceeds 100,000 cells.');
    review=book.insertSheet(name);
    chopWriteTable_(review,plan.review);
    review.getRange(1,1,plan.colors.length,13).setBackgrounds(plan.colors);
    review.setColumnWidth(1,110);review.setColumnWidths(2,12,150);review.getDataRange().setWrap(true);
    if(!alreadyPlated){
      recovery=source.copyTo(book);
      wrote=true;source.clearContents();chopWriteTable_(source,plan.metadata);
    }
    // Refresh error overlays on the working tab only.
    chopCheckSheet_(source,true);
    source.activate();
    state.prepared=true;state.reviewIds=[review.getSheetId()];
    props.setProperty('chopWorkspace',JSON.stringify(state));
    if(recovery){book.deleteSheet(recovery);recovery=null;}
    return {alreadyPlated,sampleCount:plan.sampleCount,controlCount:plan.controlCount||0,plateCount:plan.plateCount,changedIds:plan.changes?plan.changes.length:0,warning:plan.warning||''};
  }catch(error){
    const book=SpreadsheetApp.getActive();
    if(wrote&&recovery){
      try{source.clearContents();recovery.getDataRange().copyTo(source.getRange(1,1));book.deleteSheet(recovery);}
      catch(restoreError){throw new Error(error.message+' Recovery copy retained: '+recovery.getName()+'. '+restoreError.message);}
    }
    if(review)book.deleteSheet(review);
    if(previousState)PropertiesService.getDocumentProperties().setProperty('chopWorkspace',previousState);
    throw error;
  }finally{lock.releaseLock();}
}
