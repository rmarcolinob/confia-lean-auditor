"""Read-only projection comparison after synthetic school/browser activity."""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'tests')]
out=ROOT/'runtime/audit-pre10dez/school-v2';os.environ.update(json.loads((out/'server_config.json').read_text()))
from fastapi.testclient import TestClient
from confia_lean_auditor.main import app
from test_core_auth import PASSWORD
from probe_textual import checked

def client(name):
 c=TestClient(app,headers={'Origin':'http://testserver'});checked(c.post('/auth/login',json=dict(login=name,password=PASSWORD)),200);return c
teacher=client('teacher.a');manager=client('manager.a');case_root=Path(os.environ['CONFIA_TME_CASES_DIR']);cases=[]
for p in case_root.glob('case_*/case.json'):
 d=json.loads(p.read_text());cases.append(d)
result=dict(home=checked(teacher.get('/tme/home-summary?period=all'),200),management=checked(manager.get('/management/overview'),200)['metrics'],manager_catalog_status=manager.get('/problems').status_code,full_exam_case_count=sum(bool(c.get('exam_submission_id')) for c in cases),tme_human_decision_count=len(list(case_root.glob('case_*/human_decisions/*.json'))))
(out/'projection_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
