from pathlib import Path
import json,hashlib,os
from pytest import MonkeyPatch
from test_dynamic_dy3 import setup,prepared,FACTOR,FORMULA,QUESTION
from test_dynamic_dy4 import ReviewerProvider,altered
from confia_lean_auditor.dynamic.grader import DynamicSolutionGrader
from confia_lean_auditor.dynamic.review_service import DynamicReviewService
from confia_lean_auditor.submission_audits.router import service
import confia_lean_auditor.dynamic.router as router
root=Path.cwd()/'runtime/dy5-browser-final'
root.mkdir(parents=True,exist_ok=True)
m=MonkeyPatch();m.setenv('CONFIA_ASSESSMENTS_DIR',str(root/'assessments'))
_,client=setup.__wrapped__(root,m)
original=DynamicSolutionGrader.grade
rows=[]
for code,profile,text,provider,mode,question,finish in [
 ('DY5-LISTA-UP','FORMATIVE_LIST',FACTOR,ReviewerProvider(),'under',QUESTION,False),
 ('DY5-PROVA-UP','SCHOOL_EXAM',FORMULA,ReviewerProvider(refs=[['review_claim_2','review_claim_3'],['review_claim_4'],['review_claim_5','review_claim_6']],alternative=True),'under',QUESTION,True),
 ('DY5-LISTA-DOWN','FORMATIVE_LIST','y=9',ReviewerProvider(points=('0','0','0'),refs=[[],['review_claim_1'],[]],statuses=('INSUFFICIENT','NOT_SATISFIED','INSUFFICIENT')),'over',QUESTION,True),
 ('DY5-SUFICIENCIA','FORMATIVE_LIST','S={3,4}',ReviewerProvider(points=('4','3','0'),refs=[[],['review_claim_1'],[]],statuses=('COMPLETE','COMPLETE','INSUFFICIENT')),'method',QUESTION,True),
 ('DY5-LINEAR','SCHOOL_EXAM','3z=-6; z=-2; S={-2}; 3*(-2)+6=0',ReviewerProvider(refs=[['review_claim_1'],['review_claim_2','review_claim_3'],['review_claim_4']]),None,'Resolva nos reais: 3z+6=0.',True),
 ('DY5-ACORDO','SCHOOL_EXAM',FACTOR,ReviewerProvider(),None,QUESTION,True),
]:
 d=prepared(question)
 def controlled(self,*args,**kwargs):
  result=original(self,*args,**kwargs)
  if mode=='under': result=altered(result,'method',0,sufficiency='NOT_SATISFIED')
  if mode=='over': result=altered(result,'roots',3,sufficiency='COMPLETE')
  if mode=='method': result=altered(result,'method',4,sufficiency='COMPLETE',claim_ids=['claim_1'])
  if mode:
   raw=result.model_dump(mode='json')
   for item in raw['rubric_assessment']['items']:
    decision=next((c for c in raw['decisions'] if c['criterion_id']==item['id']),None)
    if decision: item['points']=float(decision['suggested_points'])
   result=type(result).model_validate(raw)
  Path(result.artifact_dir,'audit.json').write_text(result.model_dump_json(indent=2))
  return result
 m.setattr(DynamicSolutionGrader,'grade',controlled)
 response=client.post(f"/dynamic/problems/{d['problem']['problem_id']}/attempts",json=dict(external_candidate_ref=code,solution=text,allow_preparation_review=True,policy_profile=profile))
 assert response.status_code==201,response.text
 case=response.json();base=f"/tme/cases/{case['case_id']}"
 tr=client.get(base+'/transcriptions').json()[0]['transcription']['transcription_id']
 accepted=client.post(base+f'/transcriptions/{tr}/accept',json=dict(revision_number=1,reviewer_identity_verified=False)).json()
 run=client.post(base+'/audits',json=dict(transcription_id=tr,revision_number=1,acceptance_id=accepted['acceptance']['acceptance_id'])).json()
 assert run['status']=='COMPLETED',run
 m.setattr(router,'independent_review_service',lambda:DynamicReviewService(service(),provider))
 url=f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}"
 response=client.post(url+'/independent-reviews',json={'execution_key':'browser-fixture'})
 assert response.status_code==201,response.text
 review=response.json()['review'];rec=None
 if finish:
  response=client.post(url+'/reconciliations',json={'independent_review_id':review['review_id']});assert response.status_code==201,response.text;rec=response.json()['reconciliation']
 row=dict(code=code,case_id=case['case_id'],audit_run_id=run['audit_run_id'],review_id=review['review_id'],grader_score=run['result']['score'],reconciliation=rec)
 rows.append(row);print(code,case['case_id'],run['result']['score'],rec['reconciled_suggested_score'] if rec else 'pending')
(root/'scenarios.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
files=[*root.glob('audits/aud_*.json'),*root.glob('audits/independent_reviews/drev_*.json')]
(root/'before-hashes.json').write_text(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
m.undo()
