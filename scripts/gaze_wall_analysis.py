#!/usr/bin/env python3
"""Derived tables for the gaze wall-time report (ticket 1197): structure, stragglers, counterfactual seat drops, load join.

    python3 scripts/gaze_wall_analysis.py

Needs the session traces and, for the load join, sysstat files in /var/log/sysstat
(host padme: 10-minute `sar -q` samples, 2026-10-18 on). Every figure is READ
from a timestamp or derived from timestamps; see docs/2026-10-27-gaze-wall-time.md.
"""
import json,statistics as st,collections,datetime,sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
import gaze_wall_time as g
rs=sorted(g.runs(g.DEFAULT),key=lambda r:r['start'])
cut=datetime.datetime(2026,10,21,22,1).timestamp()
def P(x,p): x=sorted(x); return x[int(round(p*(len(x)-1)))]
def summ(name,rs):
    print(f'== {name}: n={len(rs)}')
    w=[r['wall'] for r in rs]; print(f'wall median {st.median(w):.0f} p90 {P(w,.9):.0f} max {max(w):.0f} total {sum(w)/60:.0f} min')
    for k in ('setup','tool','poll','model_s'):
        xs=[r[k] for r in rs if r[k] is not None]; print(f'  {k:8s} median {st.median(xs):5.0f} sum {sum(xs)/60:5.0f} min ({100*sum(xs)/sum(w):.0f}% of wall)')
    by=collections.defaultdict(list)
    for r in rs:
        for s in r['seats']: by[s['kind']].append(s['end']-s['start'])
    for k,v in sorted(by.items()): print(f"  seat {k:15s} n={len(v):3d} median {st.median(v):4.0f} p90 {P(v,.9):4.0f} max {max(v):4.0f}")
old=[r for r in rs if r['start']<cut]; new=[r for r in rs if r['start']>=cut]
summ('all',rs); summ('before 10-21 22:01',old); summ('after',new)
print('\n#### poll overshoot')
lag=[];lagbig=[]
for r in new+old:
    for (a,b) in r['polls']:
        ends=[s['end'] for s in r['seats'] if a-5<=s['end']<=b+600]
        # the seat that finished last before poll end+ (the poll exits once its last awaited seat reports)
        before=[e for e in ends if e<=b+5]
        if before:
            l=b-max(before); lag.append((l,b-a,r['start']>=cut))
for lab,sel in (('after',True),('before',False)):
    x=[l for l,d,n in lag if n==sel]
    print(lab,'polls matched',len(x),'median lag %.1f'%st.median(x),'p90 %.1f'%P(x,.9),'sum min %.1f'%(sum(x)/60), 'poll total min %.1f'%(sum(d for l,d,n in lag if n==sel)/60))
print('\n#### slow runs timeline')
def tl(r):
    t0=r['start']
    ev=[]
    for (t,d) in r['launches']: ev.append((t-t0,'launch '+d[:28]))
    for s in r['seats']: ev.append((s['end']-t0,'END '+s['kind']+' (%ds)'%(s['end']-s['start'])))
    for (a,b) in r['polls']: ev.append((a-t0,'poll>')); ev.append((b-t0,'<poll %ds'%(b-a)))
    return sorted(ev)
slow=sorted(rs,key=lambda r:-r['wall'])[:12]
print('top12 wall total min',sum(r['wall'] for r in slow)/60, 'idle gaps>120s total min',sum(sum(r['idle_gaps']) for r in slow)/60,'poll min',sum(r['poll'] for r in slow)/60)
for r in slow[:4]:
    print(r['id'],datetime.datetime.fromtimestamp(r['start']),'wall',round(r['wall']),'model',r['orch_model'])
    for t,e in tl(r): print('  %5d %s'%(t,e))
print('\n#### straggler / structure')
def struct(name,rr):
    rr=[r for r in rr if r['seats']]
    pre=[min(s['start'] for s in r['seats'])-r['start'] for r in rr]
    span=[max(s['end'] for s in r['seats'])-min(s['start'] for s in r['seats']) for r in rr]
    longest=[max(s['end']-s['start'] for s in r['seats']) for r in rr]
    post=[r['end']-max(s['end'] for s in r['seats']) for r in rr]
    sums=[sum(s['end']-s['start'] for s in r['seats']) for r in rr]
    wall=[r['wall'] for r in rr]
    print(name,'n',len(rr))
    for n,x in (('wall',wall),('pre-first-seat',pre),('seat span',span),('longest single seat',longest),('sum of seat durations',sums),('post-last-seat',post)):
        print(f'  {n:24s} median {st.median(x):5.0f} p90 {P(x,.9):5.0f} sum {sum(x)/60:5.0f} min')
    # serial: span - longest
    ex=[a-b for a,b in zip(span,longest)]
    print('  span - longest seat: median %.0f p90 %.0f sum %.0f min'%(st.median(ex),P(ex,.9),sum(ex)/60))
    c=collections.Counter(max(r['seats'],key=lambda s:s['end'])['kind'] for r in rr); print('  last seat to finish:',c.most_common())
    # polls ending near a seat end
    near=0;tot=0;lags=[]
    for r in rr:
        for a,b in r['polls']:
            if b-a<20: continue
            c2=[(abs(b-s['end']),b-s['end']) for s in r['seats'] if s['start']<b]
            if not c2: continue
            tot+=1; d,sg=min(c2)
            lags.append(sg)
            if -10<=sg<=30: near+=1
    print('  polls>=20s: %d, ending within [-10,+30]s of nearest seat end: %d'%(tot,near),'median signed lag %.1f'%st.median(lags))
struct('AFTER (current structure)',new); struct('BEFORE',old)
print('\n#### conditional phases')
for name,rr in (('AFTER',new),('BEFORE',old)):
    print(name,'results',collections.Counter(r['result'] for r in rr))
    fix=[r for r in rr if any(s['kind']=='fix' for s in r['seats'])]
    simp=[r for r in rr if any(s['kind']=='simplify' for s in r['seats'])]
    print('  runs with fix agent',len(fix),'results',collections.Counter(r['result'] for r in fix))
    print('  runs with simplify seat',len(simp),'results',collections.Counter(r['result'] for r in simp))
    nos=[r for r in rr if r['seats'] and not any(s['kind']=='simplify' for s in r['seats'])]
    print('  runs with seats but no simplify',len(nos),collections.Counter(r['result'] for r in nos))
    print('  fix agent time min: ',sum(s['end']-s['start'] for r in fix for s in r['seats'] if s['kind']=='fix')/60, ' simplify seat time min:',sum(s['end']-s['start'] for r in simp for s in r['seats'] if s['kind']=='simplify')/60)
print('\n#### counterfactual: drop one seat kind, critical path shrinks by')
def cf(name,rr):
    rr=[r for r in rr if r['seats']]
    kinds=sorted({s['kind'] for r in rr for s in r['seats']})
    print(name,'n',len(rr),'total span min',sum(max(s['end'] for s in r['seats'])-min(s['start'] for s in r['seats']) for r in rr)/60)
    for k in kinds:
        tot=0;cnt=0
        for r in rr:
            allm=max(s['end'] for s in r['seats']); rest=[s['end'] for s in r['seats'] if s['kind']!=k]
            if not rest: continue
            d=allm-max(rest)
            if d>0: tot+=d;cnt+=1
        print(f'  drop {k:15s} saves {tot/60:5.1f} min over {cnt} runs ({tot/len(rr):.0f}s per run avg)')
    # panel width: keep only adherence+correctness-ish: drop everything but adherence, semantic, correctness
    keep={'adherence','semantic','correctness'}
    tot=0
    for r in rr:
        allm=max(s['end'] for s in r['seats']); rest=[s['end'] for s in r['seats'] if s['kind'] in keep]
        if rest: tot+=max(0,allm-max(rest))
    print('  narrow panel (keep adherence, semantic, correctness only): saves %.1f min (%.0fs/run)'%(tot/60,tot/len(rr)))
cf('AFTER',new); cf('BEFORE',old)
print('\n#### orchestrator own work (AFTER epoch)')
cls=collections.defaultdict(lambda:[0,0.0])
def klass(name,arg):
    if name!='Bash': return name
    if any(k in arg for k in ('sleep','for i in','until ')): return 'poll'
    if 'pytest' in arg or 'make ' in arg: return 'tests'
    if 'git' in arg and ('diff' in arg or 'log' in arg or 'show' in arg): return 'git-read'
    if 'grep' in arg or 'rg ' in arg or 'sed -n' in arg or 'cat ' in arg: return 'read/grep'
    return 'bash-other'
for r in new:
    for (t,d,name,arg) in r['calls']:
        k=klass(name,arg); cls[k][0]+=1; cls[k][1]+=d
for k,(n,d) in sorted(cls.items(),key=lambda x:-x[1][1]): print(f'  {k:12s} calls {n:4d} tool time {d/60:5.1f} min')
print('  turns per run median',st.median(r['turns'] for r in new),' model_s/turn')
for m in ('claude-sonnet-5-5','claude-opus-5-5','claude-fable-5-1'):
    x=[r for r in rs if r['orch_model']==m and r['turns']]
    if x: print('  ',m,'runs',len(x),'model-time per turn median %.1fs'%st.median(r['model_s']/r['turns'] for r in x),' median turns',st.median(r['turns'] for r in x), 'median wall',st.median(r['wall'] for r in x))
print('after epoch models',collections.Counter(r['orch_model'] for r in new))
print('\n#### contention')
import subprocess,re,bisect
load=[]  # (epoch, ldavg1, runq)
for day in range(18,27):
    out=subprocess.run(['sar','-q','-f',f'/var/log/sysstat/sa{day}'],capture_output=True,text=True,env={'LC_ALL':'C','S_TIME_FORMAT':'ISO','PATH':'/usr/bin'}).stdout.splitlines()
    for ln in out:
        m=re.match(r'(\d\d):(\d\d):(\d\d)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)',ln)
        if m:
            h,mi,s,rq,pl,l1,l5=m.groups()
            d=datetime.datetime(2026,10,day,int(h),int(mi),int(s)).timestamp()
            load.append((d,float(l1),int(rq)))
load.sort(); print('load samples',len(load), 'range', datetime.datetime.fromtimestamp(load[0][0]),datetime.datetime.fromtimestamp(load[-1][0]), 'max ldavg1',max(l for _,l,_ in load))
ts_=[x[0] for x in load]
def L(t):
    i=bisect.bisect_left(ts_,t); i=min(max(i,0),len(load)-1); return load[i][1] if abs(ts_[i]-t)<900 else None
# global agent concurrency
import glob,os
root=os.path.expanduser('~/.claude/projects/-home-haduong--agents/')
iv=[]
for f in glob.glob(root+'*/subagents/agent-*.jsonl')+glob.glob(root+'*.jsonl'):
    try:
        with open(f,'rb') as fh:
            first=fh.readline(); fh.seek(0,2); size=fh.tell(); fh.seek(max(0,size-20000)); last=fh.read().splitlines()[-1]
        a=json.loads(first)['timestamp'] if 'timestamp' in json.loads(first) else None
        b=json.loads(last).get('timestamp')
        if a and b: iv.append((datetime.datetime.fromisoformat(a.replace('Z','+00:00')).timestamp(),datetime.datetime.fromisoformat(b.replace('Z','+00:00')).timestamp()))
    except Exception: pass
iv.sort(); starts=[x[0] for x in iv]
def conc(t):
    return sum(1 for a,b in iv if a<=t<=b)
print('agent intervals',len(iv))
rows=[]
for r in rs:
    for s in r['seats']:
        if s['kind'] in ('adherence',) and s['end']-s['start']<900:
            mid=(s['start']+s['end'])/2
            rows.append((s['end']-s['start'],L(mid),conc(mid),s['tokens'],s['model']))
rows=[x for x in rows if x[1] is not None]
print('adherence seats with load known',len(rows))
def spear(a,b):
    def rk(x):
        o=sorted(range(len(x)),key=lambda i:x[i]); r=[0]*len(x)
        for k,i in enumerate(o): r[i]=k
        return r
    ra,rb=rk(a),rk(b); n=len(a); ma=sum(ra)/n
    num=sum((x-ma)*(y-ma) for x,y in zip(ra,rb)); den=sum((x-ma)**2 for x in ra)
    return num/den
d=[x[0] for x in rows]
print('spearman(duration, ldavg1) = %.2f ; (duration, concurrent agents) = %.2f ; (duration, out tokens) = %.2f'%(spear(d,[x[1] for x in rows]),spear(d,[x[2] for x in rows]),spear(d,[x[3] for x in rows])))
lo=[x[0] for x in rows if x[1]<20]; hi=[x[0] for x in rows if x[1]>=20]
print('adherence duration: load<20 n=%d median %.0f ; load>=20 n=%d median %.0f'%(len(lo),st.median(lo),len(hi),st.median(hi) if hi else float('nan')))
c=[x[0] for x in rows if x[2]<=6]; c2=[x[0] for x in rows if x[2]>6]
print('adherence duration: conc<=6 n=%d median %.0f ; conc>6 n=%d median %.0f'%(len(c),st.median(c),len(c2),st.median(c2) if c2 else float('nan')))
# slow runs' load
for r in sorted(rs,key=lambda r:-r['wall'])[:12]:
    mid=(r['start']+r['end'])/2
    print('  slow run',datetime.datetime.fromtimestamp(r['start']).strftime('%m-%d %H:%M'),'wall',round(r['wall']),'load1',L(mid),'concurrent agents',conc(mid))
allL=[l for t,l,_ in load]; print('load1 overall median %.1f p90 %.1f max %.1f ; 64 CPUs'%(st.median(allL),P(allL,.9),max(allL)))
print('\n#### wait taxonomy')
for name,rr in (('AFTER',new),('BEFORE',old),('top12 slowest',sorted(rs,key=lambda r:-r['wall'])[:12])):
    w=sum(r['wall'] for r in rr)
    poll=sum(r['poll'] for r in rr); ag=sum(r['agent_wait'] for r in rr); tool=sum(r['tool'] for r in rr)
    print(f"{name}: wall {w/60:.0f} min; poll {poll/60:.0f} ({100*poll/w:.0f}%); foreground-agent wait {ag/60:.0f} ({100*ag/w:.0f}%); other tools {(tool-poll-ag)/60:.0f} ({100*(tool-poll-ag)/w:.0f}%); remainder (model turns, harness, notification waits; derived) {(w-tool)/60:.0f} ({100*(w-tool)/w:.0f}%)")
print('\n#### old gate+fix phases inside gaze')
g=f=0;nr=0
for r in old:
    gs=[s for s in r['seats'] if 'gate' in s['desc'].lower()]
    fs=[s for s in r['seats'] if s['kind']=='fix']
    if gs or fs: nr+=1
    g+=sum(s['end']-s['start'] for s in gs); f+=sum(s['end']-s['start'] for s in fs)
print('BEFORE runs with gate/fix phase',nr,'of',len(old),'gate seat min',g/60,'fix min',f/60,'of wall',sum(r['wall'] for r in old)/60)
# share of runs and wall in slowest decile
q=sorted(rs,key=lambda r:-r['wall'])
n10=len(q)//10
print('slowest decile n',n10,'wall min',sum(r['wall'] for r in q[:n10])/60,'of',sum(r['wall'] for r in q)/60, 'with gate/fix', sum(1 for r in q[:n10] if any('gate' in s['desc'].lower() or s['kind']=='fix' for s in r['seats'])))
# PR 1677 four rounds
print('\n#### PR 1677 rounds')
for r in rs:
    if any('1677' in s['desc'] for s in r['seats']) or any('1677' in d for _,d in r['launches']):
        print(r['id'],datetime.datetime.fromtimestamp(r['start']).strftime('%H:%M:%S'),'wall',round(r['wall']),'pre',round(min(s['start'] for s in r['seats'])-r['start']) if r['seats'] else None,'polls',[round(b-a) for a,b in r['polls'] if b-a>5],'seats',[(s['kind'],round(s['end']-s['start'])) for s in r['seats']],'turns',r['turns'],r['orch_model'])
print('\n#### setup and closing segments (AFTER, runs with seats)')
import json as J
pre_t=[];pre_tool=[];post_t=[];post_tool=[];preclass=collections.defaultdict(lambda:[0,0.0]);postclass=collections.defaultdict(lambda:[0,0.0]);ra=[]
for r in new:
    if not r['seats'] or not r['launches']: continue
    fl=min(t for t,_ in r['launches']); le=max(s['end'] for s in r['seats'])
    pc=[c for c in r['calls'] if c[0]<fl]; qc=[c for c in r['calls'] if c[0]>le]
    pre_tool.append(sum(c[1] for c in pc)); post_tool.append(sum(c[1] for c in qc))
    pre_t.append(fl-r['start']); post_t.append(r['end']-le)
    for c in pc: k=klass(c[2],c[3]); preclass[k][0]+=1; preclass[k][1]+=c[1]
    for c in qc: k=klass(c[2],c[3]); postclass[k][0]+=1; postclass[k][1]+=c[1]
    ra.append((len(pc),len(qc)))
print('n',len(pre_t),'pre-launch: median wall %.0fs of which tools %.0fs ; tool calls median %d'%(st.median(pre_t),st.median(pre_tool),st.median(a for a,b in ra)))
print('closing: median wall %.0fs of which tools %.0fs ; tool calls median %d'%(st.median(post_t),st.median(post_tool),st.median(b for a,b in ra)))
print(' pre classes',dict((k,(n,round(d))) for k,(n,d) in preclass.items()))
print(' post classes',dict((k,(n,round(d))) for k,(n,d) in postclass.items()))
print('\n#### contention, all seats, seconds per output token')
rows=[]
for r in rs:
    for s in r['seats']:
        d=s['end']-s['start']
        if s['tokens']>200 and d<1200:
            mid=(s['start']+s['end'])/2; l=L(mid)
            if l is not None: rows.append((d/s['tokens'],l,d))
print('n',len(rows),'spearman(s/token, load1)=%.2f'%spear([x[0] for x in rows],[x[1] for x in rows]),'spearman(duration, load1)=%.2f'%spear([x[2] for x in rows],[x[1] for x in rows]))
hi=[x[0] for x in rows if x[1]>=20]; lo=[x[0] for x in rows if x[1]<20]
print('s/token median: load<20 n=%d %.3f ; load>=20 n=%d %.3f'%(len(lo),st.median(lo),len(hi),st.median(hi) if hi else 0))
