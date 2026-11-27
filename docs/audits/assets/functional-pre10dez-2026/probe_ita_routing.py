"""Isolated routing reproduction using this audit's actual checks.
Provider is explicitly simulated: this proves eligibility behavior, not LLM accuracy.
No historical record is modified; rubric is deep-copied in memory.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'app'))
from confia_lean_auditor.core.schemas import AuditResponse
from confia_lean_auditor.main import validate_problem_assets,extract_student_claims
from confia_lean_auditor.claims.common.rubric_bridge import RubricClaimContext
from confia_lean_auditor.semantic_policy.ita import apply
from confia_lean_auditor.rubric.secondary_context import prepare_payload
out=ROOT/'runtime/audit-pre10dez/ita'
raw=json.loads((out/'alternative_modular.json').read_text());r=AuditResponse.model_validate(raw)
rows_path=out/'results_alternative_modular.json'
if not rows_path.exists(): rows_path=out/'results.json'
text=next(x['solution'] for x in json.loads(rows_path.read_text()) if x['variant']=='alternative_modular');assets=validate_problem_assets(ROOT/'problems/ITA2025F2Q1','ITA2025F2Q1')
context=RubricClaimContext(problem_id=r.problem_id,solution_text=text,extraction=r.extracted_claims,students=extract_student_claims(r.problem_id,text),checks=r.student_claim_checks,rubric_config=assets.rubric,statement_text=assets.problem.statement,correct_answer=assets.problem.correct_answer)
calls=[]
def simulated(request):
 calls.append(request['criterion']['id'])
 return dict(decision='met',quotes=[text],justification='SIMULAÇÃO de resposta para testar exclusivamente o roteamento dos critérios; não constitui julgamento independente.')
rubric=r.rubric_assessment.model_copy(deep=True)
payload=prepare_payload(pending=[i for i in rubric.items if i.points is None],solution=text,assets=assets,microclaims=r.microclaims,student_checks=r.student_claim_checks,claim_context=context)
apply(rubric=rubric,solution=text,assets=assets,microclaims=r.microclaims,student_claim_checks=r.student_claim_checks,claim_context=context,provider=simulated)
row=next(x for x in payload['pending_criteria'] if x['id']=='reduced_polynomial_form')
result=dict(classification='MOCK_ONLY_ROUTING_WITH_RECORDED_REAL_CHECKS',solution=text,provider_called_for=calls,remainder_candidate_evidence=row.get('candidate_evidence',[]),remainder_decision=rubric.secondary_adjudication['criteria']['reduced_polynomial_form'],score=rubric.score,items=[dict(id=i.id,points=i.points) for i in rubric.items],source_record_unchanged=json.loads((out/'alternative_modular.json').read_text())==raw)
(out/'routing_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
assert calls==['power_reductions','coefficient_system']
assert result['remainder_decision']['reason']=='no_eligible_evidence' and rubric.score is None

from confia_lean_auditor.student_claims.grounding import _math_fragment
from confia_lean_auditor.rubric.secondary_candidates import _terms
formula='(a+b)x-a'
query=' '.join([row.get('description',''),row['id'].replace('_',' '),*[x.get('description','') for x in row.get('coded_requirements',[])]])
result['cause_probes']={
 'formula_as_rhs_is_bound':_math_fragment('Assim p(x) ≡ -1+a(x-1)+bx+1 = (a+b)x-a.',formula),
 'formula_after_colon_is_bound':_math_fragment('Resto: (a+b)x-a.',formula),
 'retrieval_query':query,'query_terms':sorted(_terms(query)),
 'source_terms':sorted(_terms(text)), 'lexical_overlap':sorted(_terms(query)&_terms(text)),
 'note':'Contraste sintático apenas; nenhum parecer matemático nem fonte persistida foi alterado.'}
assert result['cause_probes']['formula_as_rhs_is_bound'] is False
assert result['cause_probes']['formula_after_colon_is_bound'] is True
assert result['cause_probes']['lexical_overlap']==[]
(out/'routing_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
