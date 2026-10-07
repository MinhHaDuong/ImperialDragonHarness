#!/usr/bin/env python3
"""Measure generated-token volume and effective response throughput from Pi sessions.
Response duration includes prefill, network and provider waiting; it is not pure decoding TPS.
Usage: python3 scripts/tournament-token-speed.py --arena ~/arena --output report.json
"""
import argparse,json,datetime,statistics
from pathlib import Path

def measure(arena,arm):
 records=[]
 for p in sorted((arena/'runs').glob('*-'+arm)):
  r=json.loads((p/'run.json').read_text())
  if r.get('verdict')!='OK':continue
  attempt=str(r.get('attempt',1));files=list((p/'attempts'/attempt/'sessions').glob('*.jsonl'))
  elapsed=0;tokens=0;calls=0
  for f in files:
   for line in f.read_text().splitlines():
    row=json.loads(line);m=row.get('message',{})
    if m.get('role')!='assistant' or not m.get('usage'):continue
    start=m.get('timestamp');end=row.get('timestamp')
    if not isinstance(start,(int,float)) or not end:continue
    dt=datetime.datetime.fromisoformat(end.replace('Z','+00:00')).timestamp()-start/1000
    if dt<=0:continue
    elapsed+=dt;tokens+=m['usage'].get('output',0);calls+=1
  records.append({'ticket':r['ticket'],'output_tokens':tokens,'response_seconds':elapsed,'calls':calls,'ticket_seconds':r['seconds']})
 return {'tickets':len(records),'mean_output_tokens':statistics.mean(x['output_tokens'] for x in records),
         'mean_response_seconds':statistics.mean(x['response_seconds'] for x in records),
         'effective_output_tps':sum(x['output_tokens'] for x in records)/sum(x['response_seconds'] for x in records),
         'mean_ticket_seconds':statistics.mean(x['ticket_seconds'] for x in records),'records':records}

def main():
 p=argparse.ArgumentParser();p.add_argument('--arena',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result={'method':'Output tokens / response wall time; includes prefill, network and provider waiting. All successful runs of selected arms. Provider tokenizers differ. No causal isolation of effort.', 'arms':{arm:measure(a.arena,arm) for arm in ('b2','d','e2','e3','l')}}
 a.output.write_text(json.dumps(result,indent=2)+'\n')
 for arm,r in result['arms'].items():print(arm,{k:round(v,2) if isinstance(v,float) else v for k,v in r.items() if k!='records'})
if __name__=='__main__':main()
