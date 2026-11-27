"""Audit-only runner: isolated stores, provider keys unavailable. Use a fresh worktree.
Run lake build before pytest; use pytest tests to avoid collecting runtime probes.
"""
import os,sys,json,subprocess,time,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[4]
name=sys.argv[1];command=sys.argv[2:]
env=os.environ.copy()
for k in list(env):
 if any(x in k for x in ('API_KEY','APP_KEY','AUTH_TOKEN','ACCESS_TOKEN')):env.pop(k,None)
for key in ('CONFIA_DYNAMIC_LLM_ENABLED','CONFIA_SEMANTIC_LLM_ENABLED','CONFIA_ENABLE_LLM_FORMAL_STEPS'):env[key]='0'
env.update(PYTHONPATH=str(root/'app'),PYTHONDONTWRITEBYTECODE='1',CONFIA_LEAN_AUDITOR_ROOT=str(root))
for key in ('AUTH','INSTITUTIONAL','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TME_EXAMS','TME_CASES','SUBMISSIONS','SUBMISSION_AUDITS','DYNAMIC','TEACHER_DECISIONS','SELF_STUDY'):
 env['CONFIA_'+key+'_DIR']=str(root/'runtime'/'audit-pre10dez'/'stores'/name/key.lower())
log=root/'runtime'/'audit-pre10dez'/f'{name}.log';started=time.time()
with log.open('w') as out:r=subprocess.run(command,cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
result=dict(name=name,command=command,exit_code=r.returncode,seconds=round(time.time()-started,2),sha256=hashlib.sha256(log.read_bytes()).hexdigest())
(root/'runtime'/'audit-pre10dez'/f'{name}.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result));sys.exit(r.returncode)
