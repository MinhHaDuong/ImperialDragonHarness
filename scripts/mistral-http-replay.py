#!/usr/bin/env python3
"""Replay a captured native request without Pi; responses stay in private files."""
import argparse,json,os,pathlib,urllib.request
p=argparse.ArgumentParser();p.add_argument('request',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
r=json.loads(a.request.read_text())
if r['url']!='https://api.mistral.ai/v1/chat/completions':p.error('Only native Mistral completions may be replayed')
key=os.environ.get('MISTRAL_API_KEY')
if not key:p.error('MISTRAL_API_KEY must be set in the environment')
a.output.mkdir(parents=True,exist_ok=True,mode=0o700)
req=urllib.request.Request(r['url'],data=json.dumps(r['body']).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(req,timeout=180) as response:
 fd=os.open(a.output/'response.sse',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as out:
  while chunk:=response.read(65536):out.write(chunk)
print('Replay response saved locally')
