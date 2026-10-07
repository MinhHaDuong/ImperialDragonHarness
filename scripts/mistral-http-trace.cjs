// Opt-in native Mistral HTTP capture. Never persist request headers.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = process.env.MISTRAL_TRACE_DIR;
if (root) {
  fs.mkdirSync(root, {recursive:true, mode:0o700});
  const baseFetch = globalThis.fetch;
  let activeFetch = baseFetch;
  const {AsyncLocalStorage} = require('node:async_hooks');
  const nested = new AsyncLocalStorage();
  const original = (...args) => nested.run(true, () => activeFetch(...args));
  let sequence=0, previous='', repeats=0;
  const hash = x => crypto.createHash('sha256').update(x).digest('hex');
  const write = (file,x) => fs.writeFileSync(file,JSON.stringify(x,null,2),{mode:0o600});
  const tracedFetch = async function(input, options) {
    if (nested.getStore()) return baseFetch(input,options);
    const url = new URL(typeof input === 'string' || input instanceof URL ? input : input.url);
    if (url.hostname !== 'api.mistral.ai' || !url.pathname.endsWith('/chat/completions'))
      return original(input,options);
    const prefix=path.join(root,`${process.pid}-${String(++sequence).padStart(6,'0')}`);
    const body=options?.body;
    if (typeof body !== 'string') throw new Error('Mistral tracer expects JSON string body');
    const payload=JSON.parse(body);
    write(prefix+'.request.json',{timestamp:new Date().toISOString(),url:url.origin+url.pathname,body:payload,body_sha256:hash(body)});
    const messages=payload.messages||[];
    const lastAssistant=messages.findLast(m=>m.role==='assistant');
    const results=[];
    for(let i=messages.length-1;i>=0 && messages[i].role==='tool';i--)
      results.unshift({name:messages[i].name,content:messages[i].content});
    const signature=hash(JSON.stringify({calls:(lastAssistant?.tool_calls||[]).map(c=>c.function),results}));
    repeats=results.length && signature===previous ? repeats+1 : results.length ? 1 : 0;
    previous=signature;
    if(repeats>=5) write(prefix+'.loop.json',{repetitions:repeats,signature,action:'observe-only',timestamp:new Date().toISOString()});
    let response;
    try { response=await original(input,options); }
    catch(error) {write(prefix+'.error.json',{name:error.name,timestamp:new Date().toISOString()});throw error;}
    const meta={status:response.status,timestamp:new Date().toISOString(),headers:{}};
    for(const k of ['x-request-id','request-id','content-type'])
      if(response.headers.has(k)) meta.headers[k]=response.headers.get(k);
    write(prefix+'.response.json',meta);
    if(!response.body)return response;
    const fd=fs.openSync(prefix+'.response.sse','wx',0o600);
    let closed=false;
    const close=()=>{if(!closed){fs.closeSync(fd);closed=true;}};
    // Forward exactly the same bytes and preserve backpressure; no clone/tee queue.
    const reader=response.body.getReader();
    const stream=new ReadableStream({
      async pull(controller) {
        try {const {value,done}=await reader.read();if(done){close();controller.close();return;}
          fs.writeSync(fd,value);controller.enqueue(value);
        }catch(error){close();controller.error(error);}
      },
      async cancel(reason){close();await reader.cancel(reason);}
    });
    return new Response(stream,{status:response.status,statusText:response.statusText,headers:response.headers});
  };
  Object.defineProperty(globalThis,'fetch',{configurable:true,get:()=>tracedFetch,set:fn=>{if(fn!==tracedFetch)activeFetch=fn;}});
}
