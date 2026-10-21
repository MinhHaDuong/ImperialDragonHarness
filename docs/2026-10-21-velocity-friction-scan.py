import json,sys,glob,os,time,collections as C,re
from datetime import datetime
cut=time.time()-14*86400
def mt(f):
    try: return os.path.getmtime(f)
    except OSError: return 0
files=[f for f in glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl')) if mt(f)>cut]
files+= [f for f in glob.glob(os.path.expanduser('~/.claude/projects/*/*/subagents/*.jsonl')) if mt(f)>cut]
err=C.Counter(); tot=C.Counter(); errmsg=C.Counter(); bashcmd=C.Counter()
gaps=C.Counter(); gapsum=C.Counter(); slow=C.Counter(); slowsum=C.Counter()
denied=C.Counter(); sleeps=0; sleepsum=0; nbash=0
def ts(s): return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
for f in files:
    sub='/subagents/' in f
    pend={}; last=None
    for l in open(f,errors='ignore'):
        try:d=json.loads(l)
        except: continue
        t=d.get('type')
        if t not in('assistant','user'):continue
        try: now=ts(d['timestamp'])
        except: now=None
        m=d.get('message',{}); c=m.get('content')
        if not isinstance(c,list): 
            last=now; continue
        for b in c:
            if b.get('type')=='tool_use':
                n=b['name']; tot[n]+=1
                pend[b['id']]=(n,b.get('input',{}),now)
                if n=='Bash':
                    nbash+=1
                    cmd=b['input'].get('command','')
                    if re.search(r'\bsleep\s+\d|--watch|gh run watch|until ',cmd): sleeps+=1
            elif b.get('type')=='tool_result':
                p=pend.pop(b.get('tool_use_id'),None)
                if not p: continue
                n,inp,t0=p
                if t0 and now:
                    dt=now-t0
                    if dt>30: slow[n]+=1; slowsum[n]+=dt
                if b.get('is_error'):
                    err[n]+=1
                    x=b.get('content'); x=x if isinstance(x,str) else json.dumps(x)
                    x=re.sub(r'[0-9a-f]{7,}|/home/\S+|\d+','N',x)[:90].replace('\n',' ')
                    errmsg[(n,x)]+=1
print('files',len(files),'bash',nbash,'sleep/watch cmds',sleeps)
print('TOOL tot/err/rate'); 
for n,k in tot.most_common(12): print(f'{n:14}{k:8}{err[n]:7}{100*err[n]/k:6.1f}%  slow>30s:{slow[n]} ({slowsum[n]/3600:.1f}h)')
print('TOP ERRORS')
for (n,x),k in errmsg.most_common(25): print(k,n,x)
