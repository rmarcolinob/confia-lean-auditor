"""Two fresh Python processes; resume and edit teacher TEXT attempt, providers OFF."""
import os,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'tests')]
out=ROOT/'runtime/audit-pre10dez/school-v2';os.environ.update(json.loads((out/'server_config.json').read_text()))
from fastapi.testclient import TestClient
from confia_lean_auditor.main import app
from test_core_auth import PASSWORD
from probe_textual import checked
from confia_lean_auditor.submission_audits.router import service
c=TestClient(app,headers={'Origin':'http://testserver'});checked(c.post('/auth/login',json=dict(login='teacher.a',password=PASSWORD)),200)
state=out/'resume_checkpoint.json'
if sys.argv[1]=='create':
 ds=checked(c.get('/dynamic/assessments'),200);doc=next(d for d in ds if d['assessment']['scope']=='TME');aid=doc['assessment']['assessment_id']
 exam=checked(c.post('/tme/exam-submissions/text',json=dict(assessment_identifier=aid,external_participant_code='SYNTHETIC-RESUME-3',idempotency_key='audit-resume-3',solutions=['3x=9; x=3'])),201)
 case=exam['question_attempts'][0];base='/tme/cases/'+case['case_id'];tr=checked(c.get(base+'/transcriptions'),200)[0];tid=tr['latest_revision']['transcription_id'];acc=checked(c.post(base+f'/transcriptions/{tid}/accept',json=dict(revision_number=1)),200)
 body=dict(execution_key='resume-1',transcription_id=tid,revision_number=1,acceptance_id=acc['acceptance']['acceptance_id']);run=checked(c.post(base+'/audits',json=body),200)
 path=service()._path(run['audit_run_id']);checkpoint=dict(base=base,body=body,run=run,artifact_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),path=str(path),exam_id=exam['submission']['submission_id'])
 state.write_text(json.dumps(checkpoint));print('CREATED_PENDING_REVIEW: persisted checkpoint; process exits before review.')
else:
 x=json.loads(state.read_text());base=x['base'];body=x['body'];old=x['run'];path=Path(x['path']);again=checked(c.post(base+'/audits',json=body),200);assert again==old;assert hashlib.sha256(path.read_bytes()).hexdigest()==x['artifact_sha256']
 tid=body['transcription_id'];checked(c.post(base+f'/transcriptions/{tid}/revisions',json=dict(based_on_revision_number=1,change_reason='Correção textual sintética para testar invalidação.',segments=[dict(segment_id='text:0',page_index=0,order=0,kind='text',text='3x=9; x=-3')])),201)
 stale=checked(c.get('/submission-audits/'+old['audit_run_id']),200)['stale'];acc=checked(c.post(base+f'/transcriptions/{tid}/accept',json=dict(revision_number=2)),200)
 new=checked(c.post(base+'/audits',json=dict(execution_key='resume-2',transcription_id=tid,revision_number=2,acceptance_id=acc['acceptance']['acceptance_id'])),200)
 assert stale and new['audit_run_id']!=old['audit_run_id'];assert hashlib.sha256(path.read_bytes()).hexdigest()==x['artifact_sha256']
 r=dict(fresh_process_resume=True,idempotent_audit=True,old_stale=stale,old_bytes_preserved=True,new_revision=new['revision_number'],old_score=old['suggested_score'],new_score=new['suggested_score'],two_audit_ids_distinct=True)
 (out/'resume_results.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
