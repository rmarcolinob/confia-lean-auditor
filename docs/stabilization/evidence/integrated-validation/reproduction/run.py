import os, sys, subprocess, json, time, platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PYTHON = '/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python'
ENV = {k:v for k,v in os.environ.items() if k in ('PATH','HOME','TMPDIR','LANG','LC_ALL','TZ')}
ENV.update(PYTHONPATH=str(ROOT/'app')+':'+str(ROOT/'tests'), CONFIA_LEAN_AUDITOR_ROOT=str(ROOT),
           CONFIA_ENABLE_LLM_FORMAL_STEPS='0', CONFIA_DYNAMIC_LLM_ENABLED='0',
           CONFIA_SEMANTIC_LLM_ENABLED='0', PYTHONHASHSEED='0')
def run(name, command, extra=None):
    env = dict(ENV, **(extra or {}))
    start = time.time()
    with (OUT/(name+'.log')).open('w') as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    record = dict(name=name, command=command, exit_code=result.returncode, seconds=round(time.time()-start,3),
                  platform=platform.platform(), python=platform.python_version(), env={k:v for k,v in env.items() if k.startswith(('CONFIA','PYTHON'))})
    (OUT/(name+'.json')).write_text(json.dumps(record,indent=2))
    print(json.dumps(record),flush=True)
    return result.returncode
if __name__ == '__main__':
    name=sys.argv[1]
    if name=='lean': sys.exit(run(name,['lake','build']))
    if name=='javascript': sys.exit(run(name,['node','--test',*map(str,sorted((ROOT/'tests/js').glob('*.cjs')))]))
    if name=='python-full': sys.exit(run(name,[PYTHON,'-m','pytest','-q','-rs','tests','--junitxml='+str(OUT/'python-full.xml')]))
    if name=='p4':
        failed=0
        for seed in range(1,31):
            failed += bool(run('p4-seed-%02d'%seed,[PYTHON,'-m','pytest','-q','tests/test_tme_accepted_integration.py::test_five_problems_accepted_engine_persistence_api[full-4]'],{'PYTHONHASHSEED':str(seed)}))
        print('FAILED_RUNS='+str(failed),flush=True)
        sys.exit(bool(failed))
    sys.exit(run(name,sys.argv[2:]))
