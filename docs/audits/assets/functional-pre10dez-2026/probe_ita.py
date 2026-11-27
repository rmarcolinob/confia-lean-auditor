"""Actual ITA extraction/checkers/Lean/current policy; no paid provider.
Reference examples are prepared fixtures, not independent validation gold.
"""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'app'))
from confia_lean_auditor.main import execute_audit
from confia_lean_auditor.core.schemas import AuditRequest

def main():
 os.environ['CONFIA_SPECIALIZED_POLICY']='semantic-b-minimal.v1'
 examples=ROOT/'problems/ITA2025F2Q1/examples'
 cases=[(name,(examples/(name+'.txt')).read_text()) for name in ('correct_solution','answer_only','missing_reduced_form','wrong_answer')]
 final=(examples/'answer_only.txt').read_text()
 cases += [('hypothesis','Suponha que '+final),('quotation','Citação não adotada: '+final),('retracted','Tentativa descartada: '+final),('false_equation','x^57=1. O resto é (a+b)x+(a+2). Portanto a=-1 e b=3.')]
 cases.append(('alternative_modular','No anel quociente por x²-x+1, temos x²=x-1 e x³=-1. Como 57=3*19, x^57=(-1)^19=-1. Como x^6=1, x^14=x^2=x-1 e x^7=x. Assim p(x) ≡ -1+a(x-1)+bx+1 = (a+b)x-a. Comparando com 2x+1: -a=1 e a+b=2. Logo a=-1 e b=3.'))
 if len(sys.argv)>1:cases=[c for c in cases if c[0]==sys.argv[1]]
 out=ROOT/'runtime/audit-pre10dez/ita';out.mkdir(parents=True,exist_ok=True);rows=[]
 for name,text in cases:
  r=execute_audit(AuditRequest(problem_id='ITA2025F2Q1',solution=text));raw=r.model_dump(mode='json');(out/(name+'.json')).write_text(json.dumps(raw,ensure_ascii=False,indent=2))
  rows.append(dict(variant=name,solution=text,score=r.score,needs_review=r.needs_review,verdict=r.verdict,rubric=raw['rubric_assessment'],lean=raw['lean_certificate'],claims=raw['student_claims'],checks=raw['student_claim_checks']))
  print(name,r.score,[(i.id,i.points) for i in r.rubric_assessment.items],flush=True)
 (out/('results_'+sys.argv[1]+'.json' if len(sys.argv)>1 else 'results.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
