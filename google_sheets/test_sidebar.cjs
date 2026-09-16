const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(__dirname+'/Sidebar.html','utf8'),nodes=new Map();
for(const [,id]of html.matchAll(/id="([^"]+)"/g))nodes.set(id,{hidden:false,setAttribute(){},addEventListener(){},replaceChildren(){}});
let requests=[],prepared=[];
const run={withFailureHandler(){return this},withSuccessHandler(fn){this.success=fn;return this},chopAutoCheck(token,restart){requests.push({restart,success:this.success});}};
const alerts=[];
const ctx={window:{alert:message=>alerts.push(message)},document:{hidden:true,getElementById:id=>nodes.get(id)},google:{script:{run}},setInterval(){}};
vm.createContext(ctx);vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],ctx);
ctx.document.hidden=false;ctx.show=()=>{};ctx.addControls=type=>prepared.push(type);
// A background skip must not consume a preparation click queued during polling.
ctx.loadState();ctx.prepareFromTab('shotgun');
requests.shift().success({skipped:true,skipReason:'Preserved original submission.'});
assert.equal(requests[0].restart,true);
requests.shift().success({passed:true,token:'working'});
assert.deepEqual(prepared,['Shotgun']);
// A direct click also carries restart intent and preserves the selected assay.
ctx.prepareFromTab('amplicon');assert.equal(requests[0].restart,true);
requests.shift().success({passed:true,token:'working'});
assert.deepEqual(prepared,['Shotgun','Amplicon']);
// A busy server returns null: polling retries the same explicit intent.
ctx.prepareFromTab('shotgun');requests.shift().success(null);ctx.loadState();
assert.equal(requests[0].restart,true);
requests.shift().success({passed:false,token:'invalid'});assert.equal(prepared.length,2);
console.log('Sidebar passed: queued clicks survive polling, direct clicks restart, lock retries preserve intent, invalid inputs do not prepare.');

assert.equal(alerts.at(-1),'Please correct the errors first and then click corresponding addControls option');

// Category labels only reveal panels, including while checking is paused after Reset.
vm.runInContext('checkingPaused=true',ctx);
const before=requests.length;
ctx.selectTab('workflow','barcode');ctx.selectTab('workflow','controls');
assert.equal(requests.length,before);
assert.equal(vm.runInContext('checkingPaused',ctx),true);
assert.equal(vm.runInContext('pendingPreparation',ctx),null);
assert.equal(nodes.get('controls-panel').hidden,false);
console.log('Category tabs only switch sections; they do not check, prepare, or resume after Reset.');
