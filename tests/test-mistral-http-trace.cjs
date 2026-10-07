const assert=require('node:assert/strict'),fs=require('node:fs');
const dir=fs.mkdtempSync('/tmp/mistral-trace-test-');process.env.MISTRAL_TRACE_DIR=dir;
let count=0;globalThis.fetch=async()=>{count++;return new Response('data: {"choices":[]}\n\ndata: [DONE]\n',{headers:{'x-request-id':'test-id'}})};
require('../scripts/mistral-http-trace.cjs');
(async()=>{
 const payload={model:'mistral-large-4',messages:[{role:'assistant',tool_calls:[{id:'abc',function:{name:'bash',arguments:'{"command":"pwd"}'}}]},{role:'tool',tool_call_id:'abc',name:'bash',content:'same output'}]};
 for(let i=0;i<6;i++) {const r=await fetch('https://api.mistral.ai/v1/chat/completions',{headers:{Authorization:'Bearer TEST_MUST_NOT_BE_LOGGED'},body:JSON.stringify(payload)});assert.equal(await r.text(),'data: {"choices":[]}\n\ndata: [DONE]\n');}
 assert.equal(count,6);const files=fs.readdirSync(dir);assert.equal(files.filter(f=>f.endsWith('.loop.json')).length,2);
 for(const f of files){const s=fs.readFileSync(dir+'/'+f,'utf8');assert(!s.includes('TEST_MUST_NOT_BE_LOGGED'));assert.equal(fs.statSync(dir+'/'+f).mode&0o777,0o600);}
 console.log('PASS: bytes preserved, six upstream calls, detector observe-only, credentials excluded, private files');
})().catch(e=>{console.error(e);process.exitCode=1});
