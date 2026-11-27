"""Synthetic text-only HTTP workflow, providers off, explicit human adjudication."""
import os, sys, json, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'artifacts/integrated-validation/platform-data'
for name in ('AUTH','INSTITUTIONAL','SUBMISSIONS','SUBMISSION_AUDITS','DYNAMIC','TME_CASES','TME_EXAMS','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TEACHER_DECISIONS','SELF_STUDY'):
    os.environ['CONFIA_'+name+'_DIR']=str(DATA/('audits' if name=='SUBMISSION_AUDITS' else name.lower()))
os.environ.update(CONFIA_AUTH_ENABLED='1',CONFIA_ENV='test',CONFIA_COOKIE_SECURE='0',CONFIA_DYNAMIC_POLICY='dynamic-semantic.v1',CONFIA_TME_DEMO_NO_AUTH='0',CONFIA_DYNAMIC_DEMO_ENABLED='0')
from test_core_auth import auth_case, PASSWORD
from fastapi.testclient import TestClient
from confia_lean_auditor.main import app

def client(login=None):
    c=TestClient(app,headers={'Origin':'http://testserver'})
    if login: assert c.post('/auth/login',json={'login':login,'password':PASSWORD}).status_code==200
    return c
def call(c,method,url,body=None,status=200):
    r=getattr(c,method)(url,**({'json':body} if body is not None else {}))
    assert r.status_code==status,(url,r.status_code,r.text)
    return r.json()
def seed():
    DATA.mkdir(parents=True)
    patch=pytest.MonkeyPatch()
    auth_case.__wrapped__(DATA,patch)
    t,s,m=client('teacher.a'),client('student.a'),client('manager.a')
    d=call(t,'post','/dynamic/assessments',dict(title='Integração PRs 7–10 — sintética textual',policy_profile='SCHOOL_EXAM'),201)
    aid=d['assessment']['assessment_id']
    p=call(t,'post','/dynamic/problems',dict(statement='Resolva 2x+6=18 e justifique.',max_score='10',correction_mode='DYNAMIC'),201)
    pid=p['problem']['problem_id']
    d=call(t,'post',f'/dynamic/assessments/{aid}/questions',dict(problem_id=pid,expected_revision=d['dynamic_revision']),201)
    call(t,'post',f'/dynamic/assessments/{aid}/activate',dict(expected_revision=d['dynamic_revision']),409)
    criteria=[dict(criterion_id='method',title='Desenvolvimento',description='Subtrair 6 e dividir ambos os membros por 2.',max_points='6',order=1),dict(criterion_id='answer',title='Resultado',description='Concluir x=6.',max_points='4',order=2)]
    p=call(t,'post',f'/dynamic/problems/{pid}/rubrics',dict(expected_revision=p['revision'],statement_version=1,max_score='10',criteria=criteria),201)
    p=call(t,'post',f'/dynamic/problems/{pid}/rubrics/{p["rubrics"][-1]["rubric_id"]}/approve',dict(expected_revision=p['revision'],acknowledge_warnings=True))
    d=call(t,'get',f'/dynamic/assessments/{aid}')
    d=call(t,'post',f'/dynamic/assessments/{aid}/activate',dict(expected_revision=d['dynamic_revision']))
    now=datetime.now(timezone.utc)
    published=call(t,'post',f'/dynamic/assessments/{aid}/institutional-publications',dict(source_definition_sha256=d['assessment']['definition_sha256'],school_id='school-a',classroom_id='class-a',opens_at=(now-timedelta(minutes=5)).isoformat(),closes_at=(now+timedelta(days=7)).isoformat(),policy=dict(max_attempts=2),execution_key='publication'),201)['assessment']
    aid=published['assessment_id']
    body=dict(definition_sha256=published['definition_sha256'],mode='TEXT',solutions=['Subtraio 6 dos dois membros: 2x=12. Divido ambos por 2 e obtenho x=6.'],execution_key='text-only')
    attempt=call(s,'post',f'/dynamic/student/activities/{aid}/attempts',body,201)
    eid=attempt['attempt_id'];cid=attempt['questions'][0]['case_id']
    assert call(s,'post',f'/dynamic/student/activities/{aid}/attempts',body)['attempt_id']==eid
    submitted=call(s,'post',f'/dynamic/student/attempts/{eid}/submit')
    assert submitted['result'] is None
    w=call(t,'get',f'/tme/question-attempts/{cid}/workspace');a=w['current_audit'];rec=a['reconciliation']
    assert rec['reconciled_suggested_score'] is None
    snapshot={str(p.relative_to(DATA)):hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.rglob('aud_*.json')}
    decision=call(t,'post',f'/tme/cases/{cid}/decision',dict(audit_run_id=a['audit_run_id'],transcription_version_id=a['transcription_version_id'],reconciliation_id=rec['reconciliation_id'],execution_key='human',decision_type='ADJUST_SCORE',final_points='10',override_reason='Adjudicação humana sintética explícita, sem inferência paga.',adjudication=dict(rubric_sha256=rec['context']['rubric_sha256'],criteria=[dict(criterion_id=c['criterion_id'],final_points=c['max_points'],justification='Professor sintético conferiu o texto e o critério.') for c in criteria])),201)
    summary=call(t,'get',f'/tme/exam-submissions/{eid}/correction');assert summary['ready_to_finalize']
    final=call(t,'post',f'/tme/exam-submissions/{eid}/correction/finalize',dict(expected_snapshot_sha256=summary['snapshot_sha256'],execution_key='final'),201)
    assert call(s,'get',f'/dynamic/student/attempts/{eid}')['result'] is None
    before=call(m,'get','/management/overview')['metrics']
    assert before['decisions_finalized_count']==1 and before['decisions_released_count']==0
    release=dict(final_correction_id=final['final_correction_id'],release_grade=True,release_feedback=True,teacher_feedback='Conferência humana sintética: resolução correta.')
    call(s,'post',f'/dynamic/school-attempts/{eid}/release',release,403)
    call(t,'post',f'/dynamic/school-attempts/{eid}/release',release)
    for c,url,status in [(client(),f'/dynamic/student/activities/{aid}',401),(client('student.b'),f'/dynamic/student/attempts/{eid}',404),(client('teacher.b'),f'/dynamic/assessments/{aid}',403),(s,f'/tme/question-attempts/{cid}/workspace',403),(m,'/management/schools/school-b/overview',403)]:
        assert c.get(url).status_code==status
    for p,digest in snapshot.items():assert hashlib.sha256((DATA/p).read_bytes()).hexdigest()==digest
    state=dict(aid=aid,eid=eid,cid=cid,audit_id=a['audit_run_id'],final_id=final['final_correction_id'],audit_hashes=snapshot,before=before)
    (DATA.parent/'platform-state.json').write_text(json.dumps(state,indent=2))
    verify()
def verify():
    state=json.loads((DATA.parent/'platform-state.json').read_text())
    s,m,t=client('student.a'),client('manager.a'),client('teacher.a')
    activity=call(s,'get','/dynamic/student/activities/'+state['aid'])
    resumed=call(s,'post','/dynamic/student/activities/'+state['aid']+'/attempts',dict(
        definition_sha256=activity['definition_sha256'],mode='TEXT',
        solutions=['Subtraio 6 dos dois membros: 2x=12. Divido ambos por 2 e obtenho x=6.'],execution_key='text-only'))
    assert resumed['attempt_id']==state['eid']
    result=call(s,'get','/dynamic/student/attempts/'+state['eid'])['result']
    assert result['final_total']=='10'
    metrics=call(m,'get','/management/overview')['metrics']
    assert metrics['submissions_count']==metrics['decisions_finalized_count']==metrics['decisions_released_count']==1,metrics
    w=call(t,'get','/tme/question-attempts/'+state['cid']+'/workspace')
    assert w['current_audit']['audit_run_id']==state['audit_id']
    for p,digest in state['audit_hashes'].items():assert hashlib.sha256((DATA/p).read_bytes()).hexdigest()==digest
    print(json.dumps(dict(stage=sys.argv[1],result=result,metrics=metrics,persistence='verified',resume_retry='same_attempt_id',audit_bytes='unchanged',provider='disabled',human_score='synthetic'),ensure_ascii=False),flush=True)
if __name__=='__main__':
    if sys.argv[1]=='seed':seed()
    elif sys.argv[1]=='verify':verify()
    elif sys.argv[1]=='serve':
        import uvicorn
        (DATA.parent/'server.pid').write_text(str(os.getpid()))
        uvicorn.run(app,host='127.0.0.1',port=int(sys.argv[2]) if len(sys.argv)>2 else 8887)
