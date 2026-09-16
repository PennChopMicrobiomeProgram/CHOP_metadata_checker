const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const ctx = vm.createContext({});
for (const name of ['Rules.gs','Validator.gs','Controls.gs']) vm.runInContext(fs.readFileSync(path.join(__dirname,name),'utf8'),ctx);
const headers=['SampleID','investigator','year_collected','time_collected','subject_id','host_species','sample_type'];
const vocab={SAMPLE_TYPE_LIST:['BAL','Blank swab','Empty well','DNA-free water','Mock DNA'],HOST_SPECIES_LIST:['Mouse',null]};
const grid=n=>[headers,...Array.from({length:n},(_,i)=>['Sample'+(i+1),'Lab','2024','12:00:00','Subject'+(i+1),'Mouse','BAL'])];
const plan=(g,run='Shotgun')=>ctx.chopPlanControls_(g,run,'20260916',vocab);
for (const n of [1,6,7,22,23,30,31,32,33,44,47,48,49,90,91,92,93,94,95,96,123,124,139,140,183,184,185,186,187,188,189,276,282,283]) {
 const p=plan(grid(n));
 assert.equal(p.plateCount,Math.ceil(n/94));
 assert.equal(p.metadata.length,1+n+p.controlCount);
 const h=p.metadata[0], id=h.indexOf('SampleID'), plate=h.indexOf('plate'), row=h.indexOf('plate_row'), col=h.indexOf('plate_column'), type=h.indexOf('sample_type');
 assert.equal(new Set(p.metadata.slice(1).map(r=>r[id])).size,p.metadata.length-1);
 assert.equal(new Set(p.metadata.slice(1).map(r=>[r[plate],r[row],r[col]].join(','))).size,p.metadata.length-1);
 for(let i=1;i<=p.plateCount;i++) {
  const onPlate=p.metadata.slice(1).filter(r=>r[plate]===String(i));
  const samples=onPlate.filter(r=>r[type]==='BAL').length;
  const controls=onPlate.filter(r=>r[type]!=='BAL');
  assert.equal(controls.length,samples>92?2:4);
  assert.ok(onPlate.length<=96);
  if(samples>92) assert.deepEqual(Array.from(controls,r=>r[type]).sort(),['DNA-free water','Mock DNA']);
 }
 const last=p.metadata.slice(1).filter(r=>r[plate]===String(p.plateCount)).length;
 assert.equal(p.lastPlateOccupancy,last);
 assert.equal(Boolean(p.warning),last<10);
 assert.equal(ctx.chopValidate(p.metadata,'add_controls',vocab).passed,true);
 // Execute the actual supplied R template as an independent placement oracle.
 if(process.env.CHOP_R_PARITY==='1' && p.controlCount===4*p.plateCount && p.plateCount===Math.ceil(n/92)) {
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'metaready-plate-'));
  const input=grid(n).map(r=>r.slice());input[0][6]='SampleType';
  fs.writeFileSync(path.join(temp,'input.tsv'),input.map(r=>r.join('\t')).join('\n')+'\n');
  const r=spawnSync('Rscript',[path.join(__dirname,'../plate_review.R'),'-w',temp,'-m','input.tsv'],{encoding:'utf8'});
  assert.equal(r.status,0,'R failed for '+n+': '+r.stderr);
  const lines=fs.readFileSync(path.join(temp,'input_withLoc.tsv'),'utf8').trimEnd().split('\n').map(l=>l.split('\t'));
  const rh=lines[0];
  const normal=(rows,head,fields)=>rows.map(r=>fields.map(f=>r[head.indexOf(f)]).map(v=>String(v).replace(/\.\d{8}$/,'.DATE')).join('|')).sort();
  assert.deepEqual(normal(Array.from(p.metadata.slice(1)),Array.from(h),['SampleID','plate','plate_row','plate_column']),normal(lines.slice(1),rh,['SampleID','plate','plate_row','plate_column']),'R placement mismatch at '+n);
 }
}
for(const run of ['Amplicon','Shotgun','WGS']) {
 const p=plan(grid(1),run);
 assert.equal(p.metadata[0].includes(run==='Amplicon'?'reverse_barcode_plate':'barcode_coord'),true);
 assert.equal(p.metadata[0].includes('date_collected'),false);
}
for (const bad of ['24','20245','20ab','05-17-24','']) {const g=grid(1);g[1][2]=bad;assert.throws(()=>plan(g),/four digits/);}
assert.throws(()=>plan([headers]),/No samples/);
const duplicated=grid(2);duplicated[2][0]=duplicated[1][0];assert.throws(()=>plan(duplicated),/duplicated/);
const collision=grid(2);collision[1][0]='A-B';collision[2][0]='A_B';assert.throws(()=>plan(collision),/duplicated/);
const generatedCollision=grid(1);generatedCollision[1][0]='mockdna1.20260916';assert.throws(()=>plan(generatedCollision),/conflicts/);
const already=grid(1);already[0]=headers.concat('plate');already[1].push('1');assert.throws(()=>plan(already),/already laid-out/);
const aliases=grid(1);aliases[0]=headers.map(h=>h==='sample_type'?'SampleType':h);assert.equal(plan(aliases).metadata[0].includes('sample_type'),true);
const cleanup=grid(1);cleanup[1][0]=' 12_A-(B) ';const cleaned=plan(cleanup);assert.equal(cleaned.changes[0].updated,'s.12.A..B');assert.equal(cleanup[1][0],' 12_A-(B) ');
console.log('Control planner passed: boundary plates, adaptive controls per plate, unique positions, output validation, aliases, ID cleanup, years and rejection paths.'+(process.env.CHOP_R_PARITY==='1'?' Actual R placement parity passed.':''));

// Google adapter contract: snapshot first, preserve source, refuse collisions,
// and roll back only newly created tabs on write failure.
function adapterCase({occupied=false, failWrite=false,plateInput=false}={}) {
 const events=[], tabs=new Map(), input=plateInput ? plateGrid() : grid(2);
 let active, nextId=10;
 function sheet(name) {
  const s={name,id:nextId++,getName:()=>s.name,getSheetId:()=>s.id,getMaxRows:()=>1000,getMaxColumns:()=>100,
   clearContents:()=>{s.values=[];},getRange:()=>range(s),getDataRange:()=>range(s),setFrozenRows:()=>{},setColumnWidth:()=>{},setColumnWidths:()=>{},
   setName:n=>{tabs.delete(s.name);s.name=n;tabs.set(n,s);events.push('rename:'+n);},
   activate:()=>{active=s;events.push('activate:'+s.name);},
   copyTo:()=>{events.push('copy:'+s.name);const b=sheet('copy');tabs.set('copy',b);return b;}};
  return s;
 }
 function range(s) { const r={getNumRows:()=>input.length,getNumColumns:()=>headers.length,getDisplayValues:()=>input,
  copyTo:()=>events.push('freeze'),setNumberFormat:()=>r,setValues:values=>{if(failWrite)throw Error('write failed');s.values=values;events.push('write:'+s.name);return r;},
  setBackgrounds:()=>r,setBackground:()=>r,setFontWeight:()=>r,setWrap:()=>r,setNote:()=>r}; return r; }
 const source=sheet('Submitted');active=source;tabs.set(source.name,source);
 if(occupied)tabs.set('metadata',sheet('metadata'));
 const book={getSheets:()=>[...tabs.values()],getActiveSheet:()=>active,getSheetByName:n=>tabs.get(n),getSpreadsheetTimeZone:()=> 'America/New_York',
  insertSheet:n=>{events.push('insert:'+n);const s=sheet(n);tabs.set(n,s);return s;},
  deleteSheet:s=>{events.push('delete:'+s.name);tabs.delete(s.name);}};
 ctx.SpreadsheetApp={getActive:()=>book,CopyPasteType:{PASTE_VALUES:'values'}};
 ctx.LockService={getDocumentLock:()=>({tryLock:()=>true,releaseLock:()=>events.push('unlock')})};
 ctx.Utilities={formatDate:()=> '20260916'};
 ctx.chopVocab_=()=>vocab;
 const props=new Map();
 ctx.PropertiesService={getDocumentProperties:()=>({setProperty:(k,v)=>props.set(k,v),getProperty:k=>props.get(k),deleteProperty:k=>props.delete(k)})};
 return {events,tabs,input,source,book,props,run:()=>ctx.chopAddControls('Shotgun',source.id)};
}
let a=adapterCase();assert.equal(a.run().controlCount,4);
assert.equal(a.events[0],'copy:Submitted');assert.equal(a.events[2],'freeze');
assert.equal(a.tabs.size,4);assert.equal(a.source.values,undefined);
assert.equal(a.tabs.get('metadata').values.length,7);
assert.equal(a.tabs.get('plate_review').values.length,10);
assert.equal(a.events.at(-1),'unlock');
a=adapterCase({occupied:true});assert.throws(a.run,/never overwritten/);assert.equal(a.tabs.size,2);assert.deepEqual(a.events,['unlock']);
a=adapterCase({failWrite:true});assert.throws(a.run,/write failed/);assert.equal(a.tabs.size,1);assert.equal(a.tabs.get('Submitted'),a.source);assert.equal(a.events.at(-1),'unlock');
console.log('Plate tab adapter passed: snapshot order, outputs, source preservation, collision refusal and rollback.');

function plateGrid(){return [
 ['SampleID','investigator','project_name','sample_type','subject_id','host_species','study_day','study_group','current_antibiotics','year_collected','time_collected','mouse_strain','cage_id','plate','plate_row','plate_column','plate_coord'],
 ['Sample1','Lab','P','BAL','Subject1','Mouse','','','','2024','12:00:00','','','P1','A','01','A1'],
 ['Control1','','P','Blank swab','','','','','','','','','','P1','G','01','G01']
];}
let g=plateGrid(), before=JSON.stringify(g);
let result=ctx.chopPlanSubmittedPlate_(g,vocab);
assert.equal(result.sampleCount,2);assert.equal(result.plateCount,1);
assert.equal(result.review[1][1],'Sample1');assert.equal(result.review[7][1],'Control1');
assert.equal(JSON.stringify(g),before);
assert.equal(ctx.chopValidate(g,'plate_template',vocab).passed,true);
assert.equal(ctx.chopIsPlateSubmission_(g,'anything'),true);
assert.equal(ctx.chopIsPlateSubmission_(grid(1),'Tube_format'),false);
// Same well with differing zero padding must be rejected.
g=plateGrid();g[2][14]='A';g[2][16]='A01';assert.throws(()=>ctx.chopPlanSubmittedPlate_(g,vocab),/Duplicate plate position/);
g=plateGrid();g[1][15]='2';assert.throws(()=>ctx.chopPlanSubmittedPlate_(g,vocab),/agree/);
g=plateGrid();g[1][16]='I13';assert.throws(()=>ctx.chopPlanSubmittedPlate_(g,vocab),/96-well/);
g=plateGrid();g[1][13]='';assert.throws(()=>ctx.chopPlanSubmittedPlate_(g,vocab),/required/);
g=plateGrid();g[2][13]='P2';result=ctx.chopPlanSubmittedPlate_(g,vocab);assert.equal(result.plateCount,2);assert.equal(result.review[17][1],'Control1');
// plate_row may be omitted when plate_coord supplies it.
g=plateGrid().map(row=>row.filter((_,i)=>i!==14));assert.equal(ctx.chopPlanSubmittedPlate_(g,vocab).sampleCount,2);
// Both aliases are ambiguous and must fail.
g=plateGrid().map((row,i)=>row.concat(i===0?'SampleType':'BAL'));assert.throws(()=>ctx.chopPlanSubmittedPlate_(g,vocab),/distinct/);
a=adapterCase({plateInput:true});const prepared=a.run();assert.equal(prepared.alreadyPlated,true);assert.equal(prepared.controlCount,0);
assert.equal(a.tabs.size,3);assert.equal(a.tabs.has('metadata'),false);assert.equal(a.tabs.has('plate_view'),true);assert.equal(a.source.values,undefined);
a=adapterCase({plateInput:true,failWrite:true});assert.throws(a.run,/write failed/);assert.equal(a.tabs.size,1);
console.log('Preplated workflow passed: customer headers, year validation, well validation, unchanged positions/IDs, multiple plates, snapshot-only output and rollback.');

// Plate and tube templates now require the same year_collected header.
g=plateGrid();g[0][9]='date_collected';assert.throws(()=>ctx.chopPlanSubmittedPlate_(g,vocab),/Missing required column: year_collected/);
for(const year of ['24','20245','20ab','05-17-24']){g=plateGrid();g[1][9]=year;assert.throws(()=>ctx.chopPlanSubmittedPlate_(g,vocab),/four digits/);}
g=plateGrid();g[1][9]='0000';assert.equal(ctx.chopPlanSubmittedPlate_(g,vocab).sampleCount,2);
console.log('Shared template headers passed: sample_type and year_collected; obsolete date-only template rejected.');

const exact94=plan(grid(94));assert.equal(exact94.plateCount,1);assert.equal(exact94.controlCount,2);assert.equal(exact94.warning,'');
assert.equal(plan(grid(188)).plateCount,2);assert.equal(plan(grid(188)).controlCount,4);
assert.equal(plan(grid(5)).warning,'Please double check number of samples, there is one plate has very few samples after adding controls');
assert.equal(plan(grid(6)).warning,'');
assert.equal(Boolean(plan(grid(95)).warning),true);
console.log('Adaptive control thresholds and exact low-occupancy warning passed.');

// Legacy reset keeps the submitted snapshot and unrelated source tab.
for(const plateInput of [false,true]){
 a=adapterCase({plateInput});a.run();
 const original=a.tabs.get('metadata_originally_submitted');
 ctx.chopResetControls();
 assert.equal(a.tabs.get('metadata_originally_submitted'),original);
 assert.equal(a.tabs.size,2);
 assert.equal(a.tabs.has('Submitted'),true);
 assert.equal(ctx.chopResetControls().paused,true);
}
// First check establishes an immutable-by-the-add-on original and a working copy.
for(const plateInput of [false,true]){
 a=adapterCase({plateInput});
 const original=a.source;
 const working=ctx.chopEnsureWorkspace_(a.book,original);
 assert.equal(original.getName(),'metadata_originally_submitted');
 assert.equal(original.values,undefined);
 assert.equal(working.getName(),'metadata');
 assert.equal(ctx.chopEnsureWorkspace_(a.book,working),working);
 assert.equal(a.tabs.size,2);
 ctx.chopCheckSheet_=sheet=>{assert.equal(sheet,working);return {passed:true};};
 const prepared=ctx.chopAddControls('Shotgun',working.id);
 assert.equal(prepared.alreadyPlated,plateInput);
 assert.equal(original.values,undefined);
 assert.equal(a.tabs.size,3);
 assert.throws(()=>ctx.chopAddControls('Amplicon',working.id),/already prepared/);
 const reset=ctx.chopResetControls();
 assert.equal(reset.paused,true);
 assert.equal(original.name,'metadata_originally_submitted');
 assert.equal(a.tabs.size,1);
 assert.equal(original.values,undefined);
 assert.equal(a.tabs.has('metadata'),false);
 const fresh=a.book.getActiveSheet();
 assert.equal(fresh.name,'metadata_originally_submitted');
 assert.equal(fresh,original);
 assert.equal(JSON.parse(a.props.get('chopWorkspace')).workingId,null);
 ctx.chopEnsureWorkspace_(a.book,fresh);
 assert.equal(a.tabs.has('metadata'),true);
}
console.log('Working-copy workflow passed: preserve before checks, in-place preparation, plated inputs, duplicate-run protection, reset and repeat submission.');

// Missing preserved source blocks deletion; partial deletion remains retryable.
a=adapterCase();let w=ctx.chopEnsureWorkspace_(a.book,a.source);
a.tabs.delete('metadata_originally_submitted');assert.throws(()=>ctx.chopResetControls(),/original input tab is missing/);assert.equal(a.tabs.has('metadata'),true);
a=adapterCase();w=ctx.chopEnsureWorkspace_(a.book,a.source);
const remove=a.book.deleteSheet; a.book.deleteSheet=()=>{throw Error('permission denied');};
assert.throws(()=>ctx.chopResetControls(),/permission denied/);
assert.equal(JSON.parse(a.props.get('chopWorkspace')).workingId,w.id);
a.book.deleteSheet=remove;ctx.chopResetControls();assert.equal(a.tabs.size,1);
console.log('Delete reset passed: preserved original, unrelated tabs, repeated reset, restart and failure retry.');

// Invalid values never block making a working copy, even for an already-named original.
a=adapterCase();a.source.setName('metadata_originally_submitted');
a.input[1][a.input[0].indexOf('year_collected')]='bad';
const invalidWorking=ctx.chopEnsureWorkspace_(a.book,a.source);
assert.equal(invalidWorking.getName(),'metadata');
assert.equal(a.source.getName(),'metadata_originally_submitted');
assert.equal(a.source.values,undefined);
assert.equal(ctx.chopValidate(a.input,'add_controls',vocab).passed,false);
console.log('Invalid submission still gets a preserved original and working copy before validation.');

// Testing often deletes metadata and renames the original back to Sheet1.
a=adapterCase();let oldWorking=ctx.chopEnsureWorkspace_(a.book,a.source);
a.book.deleteSheet(oldWorking);a.source.setName('Sheet1');
const recovered=ctx.chopEnsureWorkspace_(a.book,a.source);
assert.equal(recovered.name,'metadata');assert.notEqual(recovered.id,oldWorking.id);
assert.equal(a.source.name,'metadata_originally_submitted');
assert.equal(a.source.values,undefined);
// Never reuse a different, untracked metadata tab or ignore remaining plate outputs.
a.book.deleteSheet(recovered);a.book.insertSheet('metadata');
assert.throws(()=>ctx.chopEnsureWorkspace_(a.book,a.source),/Existing metadata tabs/);
a.book.deleteSheet(a.tabs.get('metadata'));a.book.insertSheet('plate_review');
assert.throws(()=>ctx.chopEnsureWorkspace_(a.book,a.source),/previous plate view remains/);
console.log('Stale tracking recovery passed: Sheet1 source restored safely; unrelated metadata and old reviews protected.');
