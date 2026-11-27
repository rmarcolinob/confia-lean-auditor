"""Read-only pytest observation for R1 attribution; does not change test outcomes.

Invoked in separate processes with the SAME interpreter and environment for each
source tree. subprocess.run is transparently observed for real lake/lean calls;
arguments, return values and exceptions are passed through unchanged.
"""
import datetime, hashlib, importlib.metadata, json, os, pathlib, re, subprocess, sys, time

OFFICIAL=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
BASE=pathlib.Path('/private/tmp/confia-r1-attribution-baseline-5aa7344')
OUT=OFFICIAL/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
LABEL=sys.argv[1]
ROOT=BASE if LABEL.startswith('baseline') else OFFICIAL
os.chdir(ROOT)
os.environ.pop('CONFIA_LEAN_AUDITOR_ROOT',None)
sys.path[:0]=[str(ROOT/'app'),str(ROOT)]
import pytest
def sha(data): return hashlib.sha256(data).hexdigest()
def dump(path,value): path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def norm(value):
    value=str(value)
    for root in (str(BASE),str(OFFICIAL)): value=value.replace(root,'<REPO>')
    value=re.sub(r'/private(?=/var/)', '', value)
    value=re.sub(r'/var/folders/[^\s\x27\x22]+?/pytest-of-[^/]+/pytest-\d+/([^/\s]+)', r'<PYTEST_TMP>/\1',value)
    value=re.sub(r'0x[0-9a-fA-F]+','<ADDRESS>',value)
    value=re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b','<UUID>',value)
    value=re.sub(r'(?<=artifacts/runs/)[^/\s\x27\x22]+','<RUN>',value)
    value=re.sub(r'(?<=student_claim_checks/)[^/\s\x27\x22]+\.lean','<GENERATED>.lean',value)
    return value

ORIGINAL_RUN=subprocess.run
CURRENT=None
CALLS=[]
def observed_run(*args,**kwargs):
    command=args[0] if args else kwargs.get('args')
    watch=isinstance(command,(list,tuple)) and command and pathlib.Path(str(command[0])).name in {'lake','lean'}
    if not watch: return ORIGINAL_RUN(*args,**kwargs)
    record={'nodeid':CURRENT,'command':[str(x) for x in command],'cwd':str(kwargs.get('cwd',ROOT))}
    source=pathlib.Path(str(command[-1]))
    if source.suffix=='.lean' and source.is_file():
        record.update(source_sha256=sha(source.read_bytes()),source_text=source.read_text())
    start=time.monotonic()
    try:
        result=ORIGINAL_RUN(*args,**kwargs)
        record.update(returncode=result.returncode,stdout=result.stdout or '',stderr=result.stderr or '')
        return result
    except BaseException as exc:
        record.update(exception=type(exc).__name__,message=str(exc),stdout=getattr(exc,'stdout','') or '',stderr=getattr(exc,'stderr','') or '')
        raise
    finally:
        for field in ('stdout','stderr'):
            if isinstance(record.get(field),bytes): record[field]=record[field].decode(errors='replace')
        record['duration_seconds']=time.monotonic()-start
        payload={k:norm(record.get(k)) for k in ('returncode','exception','stdout','stderr')}
        record['environment_fingerprint']=sha(json.dumps(payload,sort_keys=True).encode())
        CALLS.append(record)
        with (OUT/(LABEL+'-lean.jsonl')).open('a') as f: f.write(json.dumps(record,ensure_ascii=False)+'\n')

def environment():
    mathlib=OFFICIAL/'.lake/packages/mathlib'
    def g(*args): return ORIGINAL_RUN(['git',*args],cwd=mathlib,capture_output=True).stdout
    return {'python_executable':sys.executable,'python_version':sys.version,'cwd':str(ROOT),'path':os.environ.get('PATH'),'pythonhashseed':os.environ.get('PYTHONHASHSEED'),'packages':sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions()),'mathlib_head':g('rev-parse','HEAD').decode().strip(),'mathlib_status_sha256':sha(g('status','--porcelain=v1','-z')),'mathlib_diff_sha256':sha(g('diff','--binary','HEAD')),'lake_realpath':str((ROOT/'.lake').resolve()),'lean_inputs':{p:sha((ROOT/p).read_bytes()) for p in ('lean-toolchain','lakefile.toml','lake-manifest.json')}}

class Observer:
    def __init__(self): self.rows={}; self.collection=[]; self.collection_errors=[]
    def pytest_collection_finish(self,session): self.collection=[item.nodeid for item in session.items]
    def pytest_collectreport(self,report):
        if report.failed: self.collection_errors.append(str(report.longrepr))
    def pytest_runtest_logstart(self,nodeid,location):
        global CURRENT
        CURRENT=nodeid
    def pytest_runtest_logreport(self,report):
        row=self.rows.setdefault(report.nodeid,{'nodeid':report.nodeid,'phases':[]})
        phase={'when':report.when,'outcome':report.outcome,'duration':report.duration}
        if report.failed:
            phase['longrepr']=str(report.longrepr)
            crash=getattr(report.longrepr,'reprcrash',None)
            phase['crash']={'path':norm(crash.path),'line':crash.lineno,'message':crash.message} if crash else None
            phase['normalized_longrepr']=norm(phase['longrepr'])
            phase['traceback_fingerprint']=sha(phase['normalized_longrepr'].encode())
            errors='\n'.join(l for l in phase['normalized_longrepr'].splitlines() if l.startswith('E '))
            phase['assertion_fingerprint']=sha(json.dumps({'crash':phase['crash'] and {**phase['crash'],'message':norm(phase['crash']['message'])},'errors':errors},sort_keys=True).encode())
        row['phases'].append(phase)
        with (OUT/(LABEL+'-reports.jsonl')).open('a') as f: f.write(json.dumps({'nodeid':report.nodeid,**phase},ensure_ascii=False)+'\n')

assert not (OUT/(LABEL+'-results.json')).exists(), 'Do not overwrite an existing run'
for suffix in ('-reports.jsonl','-lean.jsonl'):
    assert not (OUT/(LABEL+suffix)).exists()
observer=Observer()
selection=json.loads((OUT/('failure-nodeids.json' if len(sys.argv)==2 else sys.argv[2])).read_text())
before=environment()
import confia_lean_auditor.dynamic.grader as grader
before['grader_file']=grader.__file__
before['grader_sha256']=sha(pathlib.Path(grader.__file__).read_bytes())
assert pathlib.Path(grader.__file__).resolve().is_relative_to(ROOT) if hasattr(pathlib.Path(),'is_relative_to') else str(ROOT) in grader.__file__
dump(OUT/(LABEL+'-environment-before.json'),before)
subprocess.run=observed_run
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
start=time.monotonic()
code=pytest.main(['-vv','--tb=long','-p','no:cacheprovider',*selection],plugins=[observer])
subprocess.run=ORIGINAL_RUN
for row in observer.rows.values():
    phases=row['phases']
    row['status']='ERROR' if any(p['outcome']=='failed' and p['when']!='call' for p in phases) else 'FAIL' if any(p['outcome']=='failed' for p in phases) else 'SKIP' if any(p['outcome']=='skipped' for p in phases) else 'PASS' if any(p['when']=='call' for p in phases) else 'INCOMPLETE'
    calls=[c for c in CALLS if c['nodeid']==row['nodeid']]
    row['lean_call_count']=len(calls)
    row['lean_environment_fingerprints']=sorted(set(c['environment_fingerprint'] for c in calls))
counts={status:sum(r['status']==status for r in observer.rows.values()) for status in ('PASS','FAIL','SKIP','ERROR','INCOMPLETE')}
dump(OUT/(LABEL+'-results.json'),{'schema':'r1-pytest-observation.v1','label':LABEL,'started_at':started,'elapsed_seconds':time.monotonic()-start,'exit_code':int(code),'selected':selection,'collected':observer.collection,'collection_errors':observer.collection_errors,'counts':counts,'tests':list(observer.rows.values()),'lean_calls':len(CALLS)})
dump(OUT/(LABEL+'-environment-after.json'),environment())
print('ATTRIBUTION_RESULT '+json.dumps(counts),flush=True)
sys.exit(code)
