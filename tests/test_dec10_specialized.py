"""Active SPECIALIZED adapters exercised offline through the existing API/stores."""
import json
from dataclasses import asdict
from pathlib import Path
import pytest
from test_score_policy_api import isolated_engine
from test_tme_accepted_integration import offline, setup, prepare, execute, solution_for, FULL
from confia_lean_auditor.semantic_policy.service import VERSION
from confia_lean_auditor.semantic_policy import service as semantic_service
from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult, AuditRequest, AuditResponse
from confia_lean_auditor.core.problem_assets import validate_problem_assets
from confia_lean_auditor.student_claims.registry import extract_student_claims
from confia_lean_auditor.rubric.positive_evidence import related_check_types
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck
from confia_lean_auditor.student_claims.grounding import source_matches
ROOT=Path(__file__).resolve().parents[1]
TEXT='P(N=n)=C(n-1,3)/2^n. P(N=n+1)/P(N=n)=n/(2*n-6). Portanto, n=6 e n=7.'


def test_ita_active_fallback_no_second_adjudication(isolated_engine,monkeypatch):
    import confia_lean_auditor.main as main
    from confia_lean_auditor.rubric import secondary_adjudicator
    monkeypatch.setenv('CONFIA_SPECIALIZED_POLICY',VERSION)
    assets=validate_problem_assets(ROOT/'problems/ITA2025F2Q6','ITA2025F2Q6')
    # Exact pipeline is unavailable in this offline functional test. The real
    # source extractor still owns claims and their source/representation binding.
    def first_pass(**kw):
        return RubricAssessment(score=None,max_score=10,items=[RubricItemResult(id=c.id,
            description=c.description,detected=False,points=None,max_points=c.points,
            mathematical_status='indeterminate') for c in assets.rubric.items])
    monkeypatch.setattr(main,'evaluate_rubric',first_pass)
    def checks(problem_id,student_claims,run_id,solution):
        return [StudentClaimCheck(id=c.id,problem_id=problem_id,claim_type=c.claim_type,
            raw_text=c.raw_text,normalized_text=c.normalized_text,lean_statement='',method=c.method,
            status='unverified',compiled=False,lean_file=None,stdout='',stderr='',data=c.data,
            grounding=c.grounding) for c in student_claims]
    monkeypatch.setattr(main,'check_student_claims_for_problem',checks)
    calls=[]
    def opinion(self,request):
        calls.append(request)
        return dict(decision='met',justification='Critério atendido segundo provider simulado.',quotes=[TEXT])
    monkeypatch.setattr(semantic_service.SemanticProvider,'__call__',opinion)
    monkeypatch.setattr(secondary_adjudicator,'adjudicate',lambda _:pytest.fail('double adjudication'))
    result=main.execute_audit(AuditRequest(problem_id='ITA2025F2Q6',solution=TEXT))
    assert calls,[(c['claim_type'],c['status'],c.get('grounding')) for c in result.student_claim_checks]
    assert result.scoring_policy==VERSION
    semantic=[i for i in result.rubric_assessment.items if i.scoring_basis=='semantic_fallback']
    assert semantic and all(i.points is None and i.suggested_points==i.max_points for i in semantic)
    assert all(i.mathematical_status=='indeterminate' for i in semantic)
    trace=json.loads((Path(result.artifact_dir)/'secondary_adjudication.json').read_text())
    assert trace['policy']==VERSION
    saved=AuditResponse.model_validate_json((Path(result.artifact_dir)/'audit.json').read_text())
    assert saved.score==result.score
    assert assets.rubric.model_dump()==validate_problem_assets(ROOT/'problems/ITA2025F2Q6','ITA2025F2Q6').rubric.model_dump()


def test_tme_accepted_pauta_fallback_and_rollback(offline,monkeypatch):
    from confia_lean_auditor.tme import accepted_audit
    from confia_lean_auditor.rubric.pauta.engine import PautaEngine
    from confia_lean_auditor.submission_audits.router import service
    client,_,_=offline
    original=accepted_audit.audit_tme
    # Simulated unavailable verification of ONE genuinely source-bound obligation.
    # All other deterministic outcomes, including the official 20-point rules,
    # are produced by the existing TME auditor.
    def unavailable(*a,**kw):
        bridge,assessment=original(*a,**kw)
        rows=list(bridge.evidence.obligations)
        i=next(i for i,e in enumerate(rows) if e.status=='supported' and e.source_claim_ids)
        rows[i]=rows[i].model_copy(update={'status':'indeterminate'})
        bridge=bridge.model_copy(update={'evidence':bridge.evidence.model_copy(update={'obligations':tuple(rows)})})
        return bridge,PautaEngine().evaluate(accepted_audit.pauta_for('TME2026P1'),bridge.evidence)
    monkeypatch.setattr(accepted_audit,'audit_tme',unavailable)
    calls=[]
    def opinion(self,request):
        calls.append(request)
        return dict(decision='met',justification='Obrigação atendida; simulação offline.',quotes=[request['solution']])
    monkeypatch.setattr(semantic_service.SemanticProvider,'__call__',opinion)
    monkeypatch.setenv('CONFIA_SPECIALIZED_POLICY',VERSION)
    base,_,_,request=prepare(client,1,solution_for(1,FULL[1]))
    run,saved=execute(client,base,request)
    assert len(calls)==1
    assert saved.result.score==20 and saved.result.max_score==20
    assert saved.result.context.semantic_policy==VERSION
    assert saved.result.pauta==accepted_audit.pauta_for('TME2026P1')
    semantic=[e for e in saved.result.bridge.evidence.obligations if e.origin=='semantic']
    assert len(semantic)==1 and semantic[0].metadata['semantic_fallback']['formal_certification'] is False
    monkeypatch.setenv('CONFIA_SPECIALIZED_POLICY','legacy')
    assert service().get(run['audit_run_id']).result.score==20
    response=client.post(base+'/audits',json=request);assert response.status_code==200,response.text
    old=response.json();assert old['audit_run_id']!=run['audit_run_id']
    assert old['result']['score']==17 and old['result']['needs_review']
    assert len(calls)==1


@pytest.mark.parametrize('decision,expected',[('met',10),('not_met',0),('review',None),('error',None)])
def test_ita_minimal_gate_preserves_unknown_and_zero(monkeypatch,decision,expected):
    from confia_lean_auditor.semantic_policy import ita
    from types import SimpleNamespace
    item=RubricItemResult(id='criterion',description='Justificar o cálculo.',detected=False,points=None,max_points=10,mathematical_status='indeterminate')
    rubric=RubricAssessment(score=None,max_score=10,items=[item])
    assets=SimpleNamespace(problem=SimpleNamespace(id='test',statement='Calcule e explique.'),
        rubric=SimpleNamespace(items=[item],model_dump=lambda **_: {'criteria':[item.model_dump(mode='json')]}))
    row={'id':'criterion','award_grounded_claims':[{'text':'2+2=4','source_span':{'start':0,'end':5},'semantic_role':'intermediate_step'}],
        'award_verification_results':[]}
    monkeypatch.setattr(ita,'prepare_payload',lambda **_: {'pending_criteria':[row]})
    def opinion(_):
        if decision=='error':raise TimeoutError()
        return dict(decision=decision,justification='Simulação offline.',quotes=['2+2=4'])
    result=ita.apply(rubric=rubric,solution='2+2=4',assets=assets,microclaims=[],student_claim_checks=[],provider=opinion)
    assert result.score==expected and result.items[0].points is None
    assert result.items[0].mathematical_status=='indeterminate'
    if decision=='error':assert result.secondary_adjudication['criteria']['criterion']['error_type']=='TimeoutError'


def test_ita_no_evidence_and_decided_items_never_call_provider(monkeypatch):
    from confia_lean_auditor.semantic_policy import ita
    from types import SimpleNamespace
    items=[RubricItemResult(id='yes',description='Verified.',detected=True,points=3,max_points=3,mathematical_status='supported'),
           RubricItemResult(id='no',description='Refuted.',detected=False,points=0,max_points=3,mathematical_status='refuted'),
           RubricItemResult(id='unknown',description='Unknown.',detected=False,points=None,max_points=4,mathematical_status='indeterminate')]
    rubric=RubricAssessment(score=None,max_score=10,items=items)
    monkeypatch.setattr(ita,'prepare_payload',lambda **_:{'pending_criteria':[{'id':'unknown'}]})
    result=ita.apply(rubric=rubric,solution='Alguma tentativa.',assets=SimpleNamespace(),microclaims=[],student_claim_checks=[],
        provider=lambda _:pytest.fail('ineligible provider call'))
    assert result.score is None
    assert [i.points for i in result.items]==[3,0,None]
