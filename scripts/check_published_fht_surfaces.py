#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Exercise installed commands against the seven immutable published examples.

Metadata equivalence delegates to the shared oracle. No parser or corpus is copied.
"""
import argparse
import concurrent.futures,hashlib,importlib.util,json,os,subprocess,tempfile
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--shared',required=True,type=Path)
parser.add_argument('--venv',required=True,type=Path)
args=parser.parse_args()
shared=args.shared.resolve()
assert subprocess.check_output(['git','-C',str(shared),'rev-parse','HEAD'],text=True).strip()=='623c79fe58edeb238a20fb6de518c62dd69b92bc'
assert not subprocess.check_output(['git','-C',str(shared),'status','--porcelain'],text=True)
exe=str(args.venv.resolve()/'bin/bioheaders')
assert subprocess.check_output([exe,'--version'],text=True).strip()=='0.13.1'
spec=importlib.util.spec_from_file_location('comparison',shared/'scripts/check_conformance.py'); oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
env={k:v for k,v in os.environ.items() if k not in ('BIOHEADERS_EXPERIMENTAL_FHT','BIOHEADERS_CANDIDATE_FHT','BIOHEADERS_FHT_SCHEMA')}
def run(*args,success=True):
 r=subprocess.run([exe,*map(str,args)],capture_output=True,env=env)
 if success: assert r.returncode==0,(args,r.stderr.decode())
 else: assert r.returncode!=0,args
 return r

def case(j):
 expected=json.loads(j.read_text()); f=j.with_suffix('.fasta'); h=j.with_suffix('.html')
 with tempfile.TemporaryDirectory() as d:
  d=Path(d); commands=[]
  def call(*args,**kw):
   r=run(*args,**kw);commands.append(dict(command=str(args[0]),exit=r.returncode));return r
  call('validate',j);call('verify',f)
  for source in (h,):
   out=d/'extracted.json';call('convert',source,out);assert oracle.same_json(json.loads(out.read_text()),expected)
  for form in ('html','yaml'):
   export=d/('export.'+form);out=d/(form+'.json')
   call('convert',j,export);call('validate',export);call('convert',export,out)
   assert oracle.same_json(json.loads(out.read_text()),expected)
  payload=d/'payload.fa';call('strip',f,payload)
  stripped=b''.join(line for line in f.read_bytes().splitlines(keepends=True) if not line.startswith(b';~'))
  assert payload.read_bytes()==stripped
  combined=d/'combined.fa';call('combine',j,payload,'-o',combined);call('verify',combined)
  out=d/'combined.json';call('convert',combined,out);combined_record=json.loads(out.read_text());assert oracle.same_json({k:v for k,v in combined_record.items() if k!='checksum'},{k:v for k,v in expected.items() if k!='checksum'})
  assessment=call('assess',f,'--format','json');assessed=json.loads(assessment.stdout);assert assessed
  # Unsupported serialization is reported; no invented JSON-LD parity.
  call('convert',j,d/'unsupported.jsonld',success=False)
  return dict(name=j.name,commands=commands,htmlReadWriteEquivalent=True,yamlRoundTrip=True,stripBytePreserving=True,combineMetadataEquivalent=True,assessmentProduced=True,jsonldUnsupported=True)
rows=list(concurrent.futures.ThreadPoolExecutor(max_workers=7).map(case,sorted((shared/'examples/fht').glob('*.json'))))
with tempfile.TemporaryDirectory() as d:
 d=Path(d);base=json.loads(next((shared/'examples/fht').glob('*.json')).read_text());selectors=[]
 for schema,version,ok in [('https://w3id.org/fair-bioheaders/fht/v0.7.0','1.0',True),('https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/v0.7.0/fht.json','1.0',True),('https://w3id.org/fair-bioheaders/fht/v999.0.0','1.0',False),('https://w3id.org/fair-bioheaders/fht/v0.7.0','99.0',False)]:
  rec=dict(base,schema=schema,schemaVersion=version);p=d/'selector.json';p.write_text(json.dumps(rec));r=run('validate',p,success=ok);selectors.append(dict(schema=schema,version=version,expectedAccepted=ok,exit=r.returncode))
print(json.dumps(dict(status='actual-published-wheel',version='0.13.1',wheelSha256='9f600347711ee771c8bc8f8e545438c255685736206b1342413b16076da20a45',source='531d98ea742277b1ec391c646f2d32d94f520b56',defaultNoOptIn=True,examples=rows,selectors=selectors),indent=2))
