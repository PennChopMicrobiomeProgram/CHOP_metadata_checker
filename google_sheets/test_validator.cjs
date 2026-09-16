const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const context = vm.createContext({});
for (const file of ['Rules.gs', 'Validator.gs', 'Code.gs', 'Controls.gs']) vm.runInContext(fs.readFileSync(__dirname + '/' + file, 'utf8'), context);
const vocab = {SAMPLE_TYPE_LIST: ['BAL', 'Buffer'], HOST_SPECIES_LIST: ['Dog', 'Fruit fly', null]};
const headers = ['SampleID','investigator','year_collected','time_collected','subject_id','host_species','sample_type','project_name','study_day','study_group','current_antibiotics','mouse_strain','cage_id'];
const good = ['Sample1','Investigator','2024','14:30:00','Subject1','Dog','BAL','Project','','','','',''];
const validate = (rows, profile='lite', cols=headers, values=vocab) => context.chopValidate([cols, ...rows], profile, values);
assert.equal(validate([good]).passed, true);
assert.equal(validate([good, good]).passed, false);
assert.equal(validate([good, good]).issues.filter(i=>i.message.startsWith('Duplicate')).length, 2);
const change = (c,v) => good.map((x,i)=>i===c?v:x);
assert.equal(validate([change(5,'')]).passed, false);
assert.equal(validate([change(4,'')]).passed, true); // dependency is directional
assert.equal(validate([change(2,'NA')]).passed, true); // Python null normalization
assert.equal(validate([change(6,'NA')]).passed, false);
assert.equal(validate([change(0,'1-a')]).issues.some(i=>i.suggestions.includes('S1.a')), true);
assert.equal(validate([change(6,'bal')]).issues.some(i=>i.suggestions.includes('BAL')), true);
assert.equal(validate([change(1,'Name ')]).passed, false);
assert.equal(validate([good], 'lite', headers, {}).passed, false);
assert.equal(validate([]).passed, false);
assert.equal(validate([good], 'lite', headers.map((h,i)=>i===0?'sample id':h)).passed, false);
assert.equal(validate([good.concat('x')], 'lite', headers.concat('SampleID')).passed, false);
const fullHeaders = headers.concat(['plate','plate_row','plate_column','BarcodeSequence']);
const full = good.concat(['P1','A','1','ATCG']);
assert.equal(validate([full],'full',fullHeaders).passed,true);
const another = full.map((x,i)=>i===0?'Sample2':i===fullHeaders.indexOf('BarcodeSequence')?'TCGA':x);
assert.equal(validate([full,another],'full',fullHeaders).issues.filter(i=>i.message.startsWith('Duplicate')).length,6);
for (const profile of ['16S','ITS','UDI']) {
 assert.equal(validate([full],profile,fullHeaders).passed,false);
 const extraHeaders=profile==='UDI'?['Primer_version','barcode_index_set','barcode_coord']:['reverse_barcode_plate','reverse_barcode_location','forward_barcode'];
 const extra=profile==='UDI'?['v1','UDI Set A','A1']:['A1','A1','ATCG'];
 assert.equal(validate([full.concat(extra)],profile,fullHeaders.concat(extraHeaders)).passed,true);
}
console.log('Validator checks passed: profiles, nulls, dependencies, duplicates, vocabularies, suggestions and headers.');

// Exercise the Google adapter with service doubles: preserve user notes and clear
// resolved checker notes without writing metadata values or cell formatting.
let grid = [headers, change(6, 'invalid')];
let notes = grid.map(r => r.map(() => ''));
notes[1][6] = 'Original lab note';
const range = {
 getNumRows: () => grid.length, getNumColumns: () => grid[0].length,
 getDisplayValues: () => grid, getNotes: () => notes.map(r => r.slice()),
 setNotes: value => { notes = value; }
};
let formatting = [];
const sheet = {getSheetId:()=>1, getName:()=> 'Metadata', getDataRange:()=>range,
 getMaxRows:()=>1000, getMaxColumns:()=>26, getLastColumn:()=>grid[0].length,
 getRange:(row,col,height,width)=>row===1&&col===1 ? range : {row,col,height,width},
 getConditionalFormatRules:()=>formatting, setConditionalFormatRules:r=>{formatting=r;}};
function builder(){
 const state={}; const b={whenFormulaSatisfied:f=>{state.formula=f;return b;},
 setBackground:c=>{state.color=c;return b;},setRanges:r=>{state.ranges=r;return b;},
 build:()=>({...state,getBooleanCondition:()=>({getCriteriaValues:()=>[state.formula]})})};return b;
}
const properties = {chopWorkspace:JSON.stringify({workingId:1}),chopProfile_1:'lite', SAMPLE_TYPE_LIST:JSON.stringify(vocab.SAMPLE_TYPE_LIST), HOST_SPECIES_LIST:JSON.stringify(vocab.HOST_SPECIES_LIST)};
context.PropertiesService = {getDocumentProperties:()=>({getProperty:key=>properties[key] || null,setProperty:(key,value)=>{properties[key]=value;}})};
context.SpreadsheetApp = {getActive:()=>({toast:()=>{}}),newConditionalFormatRule:builder};
assert.equal(context.chopCheckSheet_(sheet,false).passed,false);
assert.match(notes[1][6], /^Original lab note\n\[CHOP Metadata\]/);
grid = [headers,good];
assert.equal(context.chopCheckSheet_(sheet,false).passed,true);
assert.equal(notes[1][6],'Original lab note');
console.log('Adapter checks passed: user notes retained and resolved issue notes removed.');

// Repeated column errors collapse, keep one note, and update on edit alone.
const originalRule={getBooleanCondition:()=>null};
formatting=[originalRule];
grid=[headers,change(6,'bad'),change(6,'bad').map((v,i)=>i===0?'Sample2':v)];
notes=grid.map(r=>r.map(()=>''));
const grouped=context.chopCheckSheet_(sheet,false);
assert.equal(grouped.groupCount,1);
assert.equal(grouped.issues[0].count,2);
assert.match(notes[1][6],/CHOP Metadata/);
assert.equal(notes[2][6],'');
assert.equal(formatting[0].ranges[0].height,2);
assert.equal(formatting[1],originalRule);
const errorColor=formatting[0].color;
context.ScriptApp={AuthMode:{NONE:'NONE'}};
context.LockService={getDocumentLock:()=>({tryLock:()=>true,releaseLock:()=>{}})};
grid[1]=good;
context.onEdit({authMode:'LIMITED',range:{getSheet:()=>sheet},source:{toast:()=>{}}});
assert.equal(notes[1][6],'');
assert.match(notes[2][6],/CHOP Metadata/);
assert.equal(formatting[0].color,errorColor);
assert.equal(formatting[0].ranges[0].row,3);
grid[2][6]='BAL';
context.onEdit({authMode:'LIMITED',range:{getSheet:()=>sheet},source:{toast:()=>{}}});
assert.equal(notes[2][6],'');
assert.equal(formatting.length,1);
assert.equal(formatting[0],originalRule);
console.log('Highlight checks passed: grouping, stable colors, first-note migration, automatic edit correction and existing formatting.');

// Installed but not enabled: menu creation and installation cannot touch data.
let menus = 0;
const menu = {addItem:()=>menu, addToUi:()=>{menus++;}};
context.SpreadsheetApp = {getUi:()=>({createAddonMenu:()=>menu})};
context.PropertiesService = {getDocumentProperties:()=>{throw Error('No authorization');}};
context.ScriptApp = {AuthMode:{NONE:'NONE', LIMITED:'LIMITED'}};
context.onOpen({authMode:'NONE'});
context.onInstall({authMode:'FULL'});
context.onEdit({authMode:'NONE',range:{}});
assert.equal(menus,2);

// Document properties, not user or script properties, isolate project profiles.
let project = 'Project A';
const stores = {'Project A':{chopProfile_1:'lite'}, 'Project B':{chopProfile_1:'UDI'}};
context.PropertiesService = {getDocumentProperties:()=>({getProperty:key=>stores[project][key]||null})};
context.SpreadsheetApp = {getActive:()=>({getActiveSheet:()=>sheet,getName:()=>project}),getActiveSheet:()=>sheet};
assert.equal(context.chopState().profile,'add_controls');
project = 'Project B';
assert.equal(context.chopState().profile,'add_controls');
assert.equal(context.chopState().projectName,'Project B');
assert.throws(()=>context.chopConfigure('full',999),/active tab changed/);
project = 'Project A';
assert.equal(context.chopState().profile,'add_controls');
console.log('Add-on checks passed: authorization lifecycle, project isolation and tab-switch protection.');

// Detection follows current columns, including partial and generated layouts.
grid=[headers,good];assert.equal(context.chopDetectedProfile_(sheet),'add_controls');
grid=[headers.concat('plate'),good.concat('P1')];assert.equal(context.chopDetectedProfile_(sheet),'plate_template');
grid=[headers.concat('plate_location_combined'),good.concat('A01')];assert.equal(context.chopDetectedProfile_(sheet),'plate_template');
grid=[headers,good];assert.equal(context.chopDetectedProfile_(sheet),'add_controls');
console.log('Automatic format detection passed: tube, incomplete plate, generated plate and column changes.');

context.chopEnsureWorkspace_=(book,sheet)=>sheet;
// Automatic sidebar checking requires no saved tab profile and skips unchanged data.
let activeName='Tube_format', autoChecks=0, releases=0;
const autoSheet={getName:()=>activeName,getSheetId:()=>42,getDataRange:()=>range,getRange:()=>range,getLastColumn:()=>grid[0].length};
context.SpreadsheetApp={getActive:()=>({getActiveSheet:()=>autoSheet,getName:()=> 'Project'})};
context.PropertiesService={getDocumentProperties:()=>({getProperty:()=>null})};
context.Utilities={DigestAlgorithm:{SHA_256:'SHA_256'},computeDigest:(_,s)=>s,base64Encode:s=>s};
context.LockService={getDocumentLock:()=>({tryLock:()=>true,releaseLock:()=>releases++})};
context.chopVocab_=()=>vocab;
context.chopCheckSheet_=()=>{autoChecks++;return {passed:true};};
const autoFirst=context.chopAutoCheck(null);
assert.equal(autoChecks,1);assert.equal(releases,1);
assert.equal(context.chopAutoCheck(autoFirst.token),null);assert.equal(autoChecks,1);
grid=[headers,change(6,'bad')];context.chopAutoCheck(autoFirst.token);assert.equal(autoChecks,2);
for(const name of ['plate_review','plate_view']){
 activeName=name;assert.equal(context.chopAutoCheck(null).skipped,true);
}
assert.equal(autoChecks,2);
activeName='Another input';context.chopAutoCheck(autoFirst.token);assert.equal(autoChecks,3);
console.log('Automatic checking passed: no setup, changed input, tab changes, unchanged-data skip and preserved output tabs.');

const priorChecks=autoChecks;
grid=[['SampleID','notes'],['Example','not metadata']];
const skippedRandom=context.chopAutoCheck(null);
assert.equal(skippedRandom.skipped,true);assert.match(skippedRandom.skipReason,/Not a metadata template/);
assert.equal(autoChecks,priorChecks);
context.onEdit({range:{getSheet:()=>autoSheet}});
assert.equal(autoChecks,priorChecks);
// Header changes re-enable automatic checking without changing sheet identity.
grid=[headers,good];assert.equal(context.chopAutoCheck(skippedRandom.token).passed,true);
const missingCore=headers.filter(h=>h!=='year_collected');
grid=[missingCore,good];assert.equal(context.chopAutoCheck(null).skipped,true);
console.log('Template gating passed: random SampleID tabs untouched, missing required headers skipped, header repair resumes checks.');

// Explicit clicks on the preserved original route to its tracked working copy.
grid=[headers,good];
let active=autoSheet;
const work={...autoSheet,getSheetId:()=>43,getName:()=> 'metadata',activate:()=>{active=work;}};
context.SpreadsheetApp={getActive:()=>({getActiveSheet:()=>active,getSheets:()=>[autoSheet,work],getName:()=> 'Project'})};
let workspace={sourceId:42,workingId:43};
context.PropertiesService={getDocumentProperties:()=>({getProperty:k=>k==='chopWorkspace'?JSON.stringify(workspace):null})};
assert.equal(context.chopAutoCheck(null).passed,true);
assert.equal(active,work);
active=autoSheet;
assert.equal(context.chopAutoCheck(null,true).passed,true);
assert.equal(active,work);
// After Reset, an explicit click permits the preserved input through the guard.
active=autoSheet;workspace.workingId=null;
assert.equal(context.chopAutoCheck(null).skipped,true);
assert.equal(context.chopAutoCheck(null,true).passed,true);
console.log('Preserved-tab routing passed: passive checking leaves original alone; explicit clicks resume or use metadata.');
