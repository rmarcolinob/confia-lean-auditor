"""Real deterministic TME/Pauta/Semantic-B integration; no LLM, Lean disabled explicitly.
Prepared fixture language is NOT an independent handwritten/student corpus.
"""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'tests')]
import pytest
from test_core_auth import auth_case
from test_tme_accepted_integration import prepare,solution_for,FULL,PARTIAL,FALSE
from confia_lean_auditor.submission_audits import router as audits
from confia_lean_auditor.tme import router
from confia_lean_auditor.tme.registry import audit_tme
from confia_lean_auditor.semantic_policy.tme import apply
from confia_lean_auditor.tme.accepted_audit import pauta_for
from probe_textual import checked

def main():
 mp=pytest.MonkeyPatch();out=ROOT/'runtime/audit-pre10dez/specialized';out.mkdir(parents=True,exist_ok=True)
 for key in ('AUTH','INSTITUTIONAL','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TME_EXAMS','TME_CASES','SUBMISSIONS','SUBMISSION_AUDITS','DYNAMIC','TEACHER_DECISIONS','SELF_STUDY'):mp.setenv('CONFIA_'+key+'_DIR',str(out/key.lower()))
 mp.setenv('CONFIA_SPECIALIZED_POLICY','semantic-b-minimal.v1')
 _,_,clients,_=auth_case.__wrapped__(out,mp);client=clients('teacher.a');original=audits.service
 def factory():
  s=original();s.tme_use_lean=False;return s
 mp.setattr(audits,'service',factory);mp.setattr(router,'audit_service',factory);results=[]
 for n in range(1,6):
  problem=f'TME2026P{n}'
  variants=[('full_prepared_fixture',solution_for(n,FULL[n])),('partial',solution_for(n,[PARTIAL[n]])),('false',solution_for(n,[FALSE[n]]))]
  full=solution_for(n,FULL[n]);a=full['a'];text=a if isinstance(a,str) else a['text']
  variants += [(label,{'a':prefix+text}) for label,prefix in [('hypothesis','Suponha:\n'),('quotation','Citação:\n'),('retracted','Tentativa descartada:\n')]]
  if n>=3:variants.append(('alternative',solution_for(n,[{3:'b_tree',4:'b_parallelogram',5:'c_general'}[n]])))
  for label,solution in variants:
   base,sid,rev,request=prepare(client,n,solution)
   run=checked(client.post(base+'/audits',json=request),200);r=run.get('result');assert run['status']=='COMPLETED',(problem,label,run)
   row=dict(problem=problem,variant=label,source=solution,status=run['status'],score=r['score'],needs_review=r['needs_review'],assessment=r['assessment'],facts=r['bridge']['auditor']['facts'],obligations=r['bridge']['evidence']['obligations'],context=r['context'])
   results.append(row);print(problem,label,row['score'],[(i['item_id'],i['points_awarded']) for i in row['assessment']['items']],flush=True)
 (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));mp.undo()
if __name__=='__main__':main()
