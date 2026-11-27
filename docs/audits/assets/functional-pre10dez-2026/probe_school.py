"""Real authenticated HTTP workflow, synthetic text only, providers unavailable.
Does not simulate mathematical verdicts. Human adjudication is explicit test input.
"""
import json,os,sys,hashlib
from pathlib import Path
from datetime import datetime,timedelta,timezone
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'tests')]
import pytest
from test_core_auth import auth_case
from probe_textual import checked

def main():
 mp=pytest.MonkeyPatch();out=ROOT/'runtime/audit-pre10dez/school-v2';out.mkdir(parents=True,exist_ok=True)
 for key in ('AUTH','INSTITUTIONAL','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TME_EXAMS','TME_CASES','SUBMISSIONS','SUBMISSION_AUDITS','DYNAMIC','TEACHER_DECISIONS','SELF_STUDY'):mp.setenv('CONFIA_'+key+'_DIR',str(out/key.lower()))
 mp.setenv('CONFIA_DYNAMIC_POLICY','dynamic-semantic.v1');mp.setenv('CONFIA_SPECIALIZED_POLICY','semantic-b-minimal.v1')
 _,users,clients,_=auth_case.__wrapped__(out,mp);t=clients('teacher.a');s=clients('student.a');m=clients('manager.a');evidence={}
 p=checked(t.post('/dynamic/problems',json=dict(title='Equação sintética — auditoria',statement='Resolva nos reais: 3x-9=0.',max_score='10',correction_mode='DYNAMIC')),201)
 pid=p['problem']['problem_id'];criteria=[dict(criterion_id='method',title='Desenvolvimento',description='Justificar a resolução por transformações equivalentes.',max_points='6',order=1),dict(criterion_id='answer',title='Resultado',description='Obter todas as raízes reais.',max_points='4',order=2)]
 p=checked(t.post(f'/dynamic/problems/{pid}/rubrics',json=dict(expected_revision=p['revision'],statement_version=1,max_score='10',criteria=criteria)),201)
 evidence['before_approval_attempt']=t.post(f'/dynamic/problems/{pid}/attempts',json=dict(external_candidate_ref='SYNTHETIC',solution='3x=9; x=3')).status_code
 p=checked(t.post(f"/dynamic/problems/{pid}/rubrics/{p['rubrics'][-1]['rubric_id']}/approve",json=dict(expected_revision=p['revision'],acknowledge_warnings=True)),200)
 a=checked(t.post('/dynamic/assessments',json=dict(title='Atividade sintética de auditoria',instructions='Explique os passos.',policy_profile='SCHOOL_EXAM')),201)
 aid=a['assessment']['assessment_id'];a=checked(t.post(f'/dynamic/assessments/{aid}/questions',json=dict(expected_revision=a['dynamic_revision'],problem_id=pid)),201)
 a=checked(t.post(f'/dynamic/assessments/{aid}/activate',json=dict(expected_revision=a['dynamic_revision'])),200)
 now=datetime.now(timezone.utc);a=checked(t.post(f'/dynamic/assessments/{aid}/institutional-publications',json=dict(source_definition_sha256=a['assessment']['definition_sha256'],school_id='school-a',classroom_id='class-a',opens_at=(now-timedelta(minutes=5)).isoformat(),closes_at=(now+timedelta(days=7)).isoformat(),policy=dict(max_attempts=2),execution_key='audit-publish')),201)['assessment'];aid=a['assessment_id']
 attempt_body=dict(definition_sha256=a['definition_sha256'],mode='TEXT',solutions=['3x=9; x=3'],execution_key='audit-attempt')
 attempt=checked(s.post(f'/dynamic/student/activities/{aid}/attempts',json=attempt_body),201);eid=attempt['attempt_id'];cid=attempt['questions'][0]['case_id']
 sent=checked(s.post('/dynamic/student/attempts/'+eid+'/submit'),200);evidence['pre_release_result']=sent['result'];evidence['submitted_status']=sent['questions'][0]['status']
 w=checked(t.get('/tme/question-attempts/'+cid+'/workspace'),200);ar=w['current_audit'];rec=ar['reconciliation'];evidence['automatic']={k:ar.get(k) for k in ('suggested_score','status','audit_run_id')};evidence['automatic']['reconciled_score']=rec['reconciled_suggested_score'];evidence['automatic']['technical_uncertainty']=rec['technical_uncertainty']
 before={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'audits').rglob('*.json')}
 body=dict(audit_run_id=ar['audit_run_id'],transcription_version_id=ar['transcription_version_id'],reconciliation_id=rec['reconciliation_id'],execution_key='audit-human',decision_type='ADJUST_SCORE',final_points='10',override_reason='Avaliação humana sintética: 3x=9 é transformação equivalente; x=3 é a única raiz.',adjudication=dict(rubric_sha256=rec['context']['rubric_sha256'],criteria=[dict(criterion_id='method',final_points='6',justification='Subtrair o termo constante de ambos os membros produz 3x=9.'),dict(criterion_id='answer',final_points='4',justification='Dividir ambos os membros por 3 produz a única raiz real x=3.')]))
 decision=checked(t.post('/tme/cases/'+cid+'/decision',json=body),201)
 summary=checked(t.get(f'/tme/exam-submissions/{eid}/correction'),200);assert summary['ready_to_finalize']
 final=checked(t.post(f'/tme/exam-submissions/{eid}/correction/finalize',json=dict(expected_snapshot_sha256=summary['snapshot_sha256'],execution_key='audit-final')),201)
 evidence['final_human_score']=final['final_total'];evidence['before_explicit_release']=checked(s.get('/dynamic/student/attempts/'+eid),200)['result']
 release=dict(final_correction_id=final['final_correction_id'],release_grade=True,release_feedback=True,teacher_feedback='As operações preservam a igualdade. Confira a substituição na equação original.')
 evidence['student_release_denied']=s.post('/dynamic/school-attempts/'+eid+'/release',json=release).status_code
 checked(t.post('/dynamic/school-attempts/'+eid+'/release',json=release),200);evidence['released_result']=checked(s.get('/dynamic/student/attempts/'+eid),200)['result']
 evidence['isolation']={'other_student':clients('student.b').get('/dynamic/student/attempts/'+eid).status_code,'other_school_teacher':clients('teacher.b').get('/dynamic/assessments/'+aid).status_code,'student_workspace':s.get('/tme/question-attempts/'+cid+'/workspace').status_code,'anonymous':clients().get('/dynamic/student/activities/'+aid).status_code,'manager_other_school':m.get('/management/schools/school-b/overview').status_code}
 evidence['management']=checked(m.get('/management/overview'),200)['metrics'];evidence['persisted_tme_human_decisions']=len(list((out/'tme_cases').rglob('human_decisions/*.json')));evidence['persisted_generic_teacher_decisions']=len(list((out/'teacher_decisions').rglob('*.json')))
 evidence['audit_bytes_preserved']=all(hashlib.sha256((out/p).read_bytes()).hexdigest()==h for p,h in before.items());evidence['idempotent_same_attempt']=checked(s.post(f'/dynamic/student/activities/{aid}/attempts',json=attempt_body),200)['attempt_id']==eid
 evidence['seed']={'assessment_id':aid,'attempt_id':eid,'case_id':cid,'problem_id':pid}
 (out/'results.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
 # Explicit safe environment for a separate real ASGI process; no inherited credentials.
 config={k:v for k,v in os.environ.items() if k.startswith('CONFIA_') and (k.endswith('_DIR') or k in ('CONFIA_AUTH_ENABLED','CONFIA_COOKIE_SECURE','CONFIA_ENV','CONFIA_DYNAMIC_POLICY','CONFIA_SPECIALIZED_POLICY','CONFIA_DYNAMIC_LLM_ENABLED','CONFIA_SEMANTIC_LLM_ENABLED','CONFIA_ENABLE_LLM_FORMAL_STEPS','CONFIA_LEAN_AUDITOR_ROOT'))}
 (out/'server_config.json').write_text(json.dumps(config,indent=2));print(json.dumps(evidence,ensure_ascii=False));mp.undo()
if __name__=='__main__':main()
