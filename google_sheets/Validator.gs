/* Pure validation engine. No Google services or metadata transmission. */
function chopRules(profile) {
  if (profile === 'plate_template') return chopRules('add_controls');
  if (profile === 'add_controls') {
    // Pre-submission columns plus full metadata value/uniqueness checks when present.
    return CHOP_RULES.specs_lite.concat(CHOP_RULES.specs_common.filter(r =>
      r.kind !== 'columns_named' && !CHOP_RULES.specs_lite.some(x => JSON.stringify(x) === JSON.stringify(r))));
  }
  const groups = {
    lite: ['specs_lite'], full: ['specs_common', 'specs_common_strict'],
    internal: ['specs_common'],
    '16S': ['specs_common', 'specs_common_strict', 'specs_16S'],
    ITS: ['specs_common', 'specs_common_strict', 'specs_ITS'],
    UDI: ['specs_common', 'specs_common_strict', 'specs_UDI']
  };
  if (!groups[profile]) throw new Error('Choose a valid checking profile.');
  return groups[profile].flatMap(g => CHOP_RULES[g]);
}

function chopValidate(grid, profile, vocab) {
  const rules = chopRules(profile);
  const issues = [], originalHeaders = grid[0] || [];
  const headers = originalHeaders.map(h => h === 'SampleType' ? 'sample_type' : (h === 'plate_location_combined' ? 'plate_coord' : h));
  const nulls = new Set(['', '0000-00-00', 'Null', 'null', 'NA', 'N/A', 'na', 'n/a', 'None', 'none']);
  const rows = grid.slice(1).map(r => headers.map((_, c) => {
    const v = String(r[c] == null ? '' : r[c]);
    return nulls.has(v) ? null : v;
  }));
  function add(row, col, message, suggestions) {
    issues.push({row, col, field: originalHeaders[col - 1] || 'Header', message, suggestions: suggestions || []});
  }
  const required = [...new Set(rules.filter(r => r.kind === 'columns_named').flatMap(r => r.args[0]))];
  headers.forEach((h, c) => {
    if (!h || headers.indexOf(h) !== c) add(1, c + 1, 'Every column needs a distinct, nonempty header.');
    const canonical = required.find(x => x.toLowerCase().replace(/[^a-z0-9]/g, '') === h.toLowerCase().replace(/[^a-z0-9]/g, ''));
    if (canonical && canonical !== h) add(1, c + 1, 'Use the exact standard header.', [canonical]);
  });
  if (!rows.length || !rows.some(r => r.some(v => v !== null))) add(1, 1, 'Enter at least one sample before sharing.');
  if (profile === 'add_controls' && headers.some(h => ['plate','plate_row','plate_column'].includes(h))) {
    ['plate','plate_row','plate_column','BarcodeSequence'].filter(h => !headers.includes(h))
      .forEach(h => add(1,1,'Missing required column: ' + h,[h]));
  }
  if (profile === 'plate_template') chopPlatePositions_(grid).issues.forEach(i => issues.push(i));
  rules.forEach(rule => {
    const a = rule.args, kind = rule.kind;
    if (kind === 'columns_named') {
      a[0].filter(h => !headers.includes(h)).forEach(h => add(1, 1, 'Missing required column: ' + h, [h]));
      return;
    }
    if (kind === 'columns_matching') {
      headers.forEach((h, c) => { if (!new RegExp(a[0]).test(h)) add(1, c + 1, 'Headers may contain only letters, numbers, underscores, periods and dashes.'); });
      return;
    }
    if (kind === 'unique_values_for' || kind === 'some_value_for') {
      const cols = a.map(h => headers.indexOf(h));
      if (cols.includes(-1)) return;
      if (kind === 'some_value_for') {
        rows.forEach((r, i) => {
          if (cols.slice(0, -1).every(c => !!r[c]) && !r[cols[cols.length - 1]])
            add(i + 2, cols[cols.length - 1] + 1, a.length === 1 ? 'This value is required.' : 'Fill in ' + a[a.length - 1] + ' when ' + a.slice(0, -1).join(' and ') + ' is filled in.');
        });
      } else {
        const seen = new Map();
        rows.forEach((r, i) => {
          const values = cols.map(c => r[c]);
          if (!values.some(Boolean)) return;
          const key = JSON.stringify(values);
          if (!seen.has(key)) seen.set(key, []);
          seen.get(key).push(i + 2);
        });
        seen.forEach(indices => {
          if (indices.length > 1) indices.forEach(row => cols.forEach(c => add(row, c + 1, 'Duplicate ' + a.join(' + ') + ' in rows ' + indices.join(', ') + '. Verify the original records; each must be unique.')));
        });
      }
      return;
    }
    const c = headers.indexOf(a[0]);
    if (c < 0) return;
    let allowed;
    if (kind === 'values_in_set') {
      allowed = Array.isArray(a[1]) ? a[1] : vocab[a[1].vocabulary];
      if (!allowed || !allowed.some(v => v !== null)) {
        add(1, c + 1, 'Allowed values unavailable. Ask the template owner to refresh allowed values.');
        return;
      }
    }
    rows.forEach((r, i) => {
      const v = r[c];
      if (kind === 'values_in_set' && !allowed.includes(v)) {
        const norm = x => String(x).toLowerCase().replace(/[^a-z0-9]/g, '');
        const matches = allowed.filter(x => x !== null && norm(x) === norm(v));
        add(i + 2, c + 1, 'Choose an allowed value from the dropdown. Allowed: ' + allowed.filter(x => x !== null).join(', '), matches);
      }
      if (kind === 'values_matching' && v !== null && !new RegExp(a[1]).test(v)) {
        const help = {
          SampleID: 'Start with a letter; use only letters, numbers, underscores and periods.',
          subject_id: 'Start with a letter; use only letters, numbers, underscores, periods and dashes.',
          year_collected: 'Use exactly four digits, for example 2024.',
          time_collected: 'Use HH:MM:SS in 24-hour time, for example 14:30:00.',
          BarcodeSequence: 'Use uppercase nucleotide symbols: ATCGURYKMSWBDHVN.',
          reverse_barcode_plate: 'Use an uppercase letter followed by one or two digits, for example A1.',
          barcode_index_set: 'Use UDI Set A, UDI Set B, UDI Set C or UDI Set D.',
          barcode_coord: 'Use A–H followed by one or two digits, for example A1.'
        };
        let suggestion = v.trim();
        if (a[0] === 'SampleID' || a[0] === 'subject_id') {
          if (!/^[A-Za-z]/.test(suggestion)) suggestion = (a[0] === 'SampleID' ? 'S' : 'SB') + suggestion;
          suggestion = suggestion.replace(a[0] === 'SampleID' ? /[^0-9A-Za-z._]/g : /[^0-9A-Za-z._-]/g, '.');
        }
        if (a[0] === 'BarcodeSequence') suggestion = suggestion.toUpperCase();
        add(i + 2, c + 1, help[a[0]] || 'Required format: ' + a[1], suggestion !== v && new RegExp(a[1]).test(suggestion) ? [suggestion] : []);
      }
    });
  });
  rows.forEach((r, i) => r.forEach((v, c) => {
    if (v && v.trim() !== v) add(i + 2, c + 1, 'Remove spaces at the beginning or end.', [v.trim()]);
  }));
  return {issues, passed: issues.length === 0, samples: rows.length, profile};
}

// Normalize positions only for comparison and display; never rewrite the input.
function chopPlatePositions_(grid) {
  const h=(grid[0]||[]).map(h=>h==='plate_location_combined'?'plate_coord':h), issues=[], placements=[], seen=new Map();
  const add=(row,field,message)=>issues.push({row,col:Math.max(1,h.indexOf(field)+1),field,message,suggestions:[]});
  for(const field of ['SampleID','plate','plate_column','plate_coord'])
    if(!h.includes(field)) add(1,field,'Missing required column: '+field);
  if(issues.length) return {issues,placements};
  const value=(r,key)=>String(r[h.indexOf(key)]==null?'':r[h.indexOf(key)]);
  grid.slice(1).forEach((r,i)=>{
    if(r.every(v=>v==null||String(v)===''))return;
    const row=i+2, plate=value(r,'plate'), coord=value(r,'plate_coord'), id=value(r,'SampleID');
    if(!id) add(row,'SampleID','This value is required.');
    if(!plate.trim()||['NA','N/A','null','None'].includes(plate)) add(row,'plate','This value is required.');
    const match=/^([A-H])(0?[1-9]|1[0-2])$/.exec(coord);
    if(!match) {add(row,'plate_coord','Use a 96-well coordinate A1–H12 (A01 is also accepted).');return;}
    const column=value(r,'plate_column');
    if(!/^(0?[1-9]|1[0-2])$/.test(column)||Number(column)!==Number(match[2]))
      add(row,'plate_column','plate_column must be 1–12 and agree with plate_coord.');
    if(h.includes('plate_row')&&value(r,'plate_row')!==match[1])
      add(row,'plate_row','plate_row must be A–H and agree with plate_coord.');
    const key=JSON.stringify([plate.trim(),match[1],Number(match[2])]);
    if(!seen.has(key))seen.set(key,[]);
    seen.get(key).push(row);
    placements.push({plate, row:match[1], column:Number(match[2]), id,
      type:value(r,h.includes('SampleType')?'SampleType':'sample_type')});
  });
  seen.forEach(rows=>{if(rows.length>1)rows.forEach(row=>add(row,'plate_coord','Duplicate plate position in rows '+rows.join(', ')+'.'));});
  return {issues,placements};
}
