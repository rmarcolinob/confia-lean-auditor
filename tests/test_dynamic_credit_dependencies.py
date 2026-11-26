"""Generic novel-problem contracts: all mathematical opinions below are simulated."""
from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace
import json
import pytest
from test_dynamic_dy3 import setup, attempt, ACTOR
from confia_lean_auditor.dynamic.models import CreateProblem,SaveRubric,ApproveRubric,RubricCriterion,RubricContent
from confia_lean_auditor.dynamic.store import dynamic_store
from confia_lean_auditor.dynamic.semantic_credit import DynamicCreditProvider
from confia_lean_auditor.semantic_policy.service import SemanticProvider,DYNAMIC_VERSION
from confia_lean_auditor.submission_audits.router import service
from confia_lean_auditor.dynamic.dependencies import assess_dependencies

LAGRANGE='Encontre os extremos de f(x,y)=xy sujeitos a x²+y²=1, justificando o método.'
WORK='Uso multiplicadores de Lagrange. L=xy-λ(x²+y²-1). y=2λx, x=2λy, x²+y²=1. Multiplicando as equações por x e y, xy=2λx²=2λy². Se λ=0 então x=y=0, impossível na restrição. Logo x²=y². Daí concluo x=2y. Concluo máximo 1/2.'


def criterion(cid,points,order,**extra):
    return dict(criterion_id=cid,title=cid,description='Justificar matematicamente '+cid,max_points=str(points),order=order,**extra)


def problem(criteria,statement=LAGRANGE):
    store=dynamic_store();maximum=str(sum(Decimal(c['max_points']) for c in criteria))
    d=store.create(CreateProblem(statement=statement,max_score=maximum,correction_mode='DYNAMIC'),ACTOR)
    d=store.save_rubric(d['problem']['problem_id'],SaveRubric(expected_revision=d['revision'],statement_version=1,max_score=maximum,criteria=criteria),ACTOR)
    return store.approve(d['problem']['problem_id'],d['rubrics'][-1]['rubric_id'],ApproveRubric(expected_revision=d['revision']),ACTOR)


def opinion(state='met',level=None,finding=None,dependency='satisfied'):
    return dict(decision=state,level_id=level,finding=finding or ('VALID_ARGUMENT' if state in {'met','partial'} else 'MATHEMATICAL_ERROR' if state=='not_met' else 'UNCERTAIN'),dependency=dependency)


def simulated(monkeypatch, grader=None, reviewer=None):
    calls=[]
    def call(self,request):
        calls.append(deepcopy(request));cid=request['criterion']['criterion_id']
        selected=(reviewer if request['stage']=='independent_reviewer' and reviewer is not None else grader) or {}
        item=selected.get(cid,opinion());item=opinion(item) if isinstance(item,str) else dict(item)
        if item['decision']=='error':raise TimeoutError('simulated provider failure')
        self.metadata=dict(provider='controlled-test',model='simulation',llm_used=False,response_id='simulated-'+str(len(calls)))
        response=dict(decision=item['decision'],justification='Parecer matemático simulado, baseado no trecho do aluno.',quotes=item.pop('quotes',[request['solution']]))
        if request.get('credit_contract'):
            response.update(level_id=item.get('level_id'),finding=item.get('finding','VALID_ARGUMENT'),dependencies=[dict(criterion_id=d['criterion_id'],status=item.get('dependency','satisfied'),justification='Condição aprovada conferida no trecho.',quotes=[request['solution']]) for d in request['criterion'].get('dependency_rules',[])])
        return response
    monkeypatch.setattr(SemanticProvider,'__call__',call)
    monkeypatch.setattr(DynamicCreditProvider,'__call__',call)
    return calls


def flow(setup,monkeypatch,criteria,grader=None,reviewer=None,statement=LAGRANGE,solution=WORK):
    _,client=setup;monkeypatch.setenv('CONFIA_DYNAMIC_POLICY',DYNAMIC_VERSION)
    calls=simulated(monkeypatch,grader,reviewer)
    doc=problem(criteria,statement);case,base,body=attempt(client,doc,solution)
    response=client.post(base+'/audits',json=body);assert response.status_code==200,response.text
    run=response.json();assert run['status']=='COMPLETED',run
    cid=case['case_id'];url=f"/dynamic/attempts/{cid}/audits/{run['audit_run_id']}"
    assert client.post(f'/dynamic/attempts/{cid}/policy',json={'policy_profile':'SCHOOL_EXAM'}).status_code==201
    r=client.post(url+'/independent-reviews',json={'execution_key':'blind'});assert r.status_code==201,r.text
    review=r.json()['review'];assert review['status']=='COMPLETED',review
    r=client.post(url+'/reconciliations',json={'independent_review_id':review['review_id']});assert r.status_code==201,r.text
    return client,case,service().get(run['audit_run_id']),review,r.json()['reconciliation'],calls


def partial(cid='work',points='4',order=1,**kw):
    return criterion(cid,points,order,credit_levels=[dict(level_id='initial',points=str(Decimal(points)/2),description='Etapa inicial válida e justificada; desenvolvimento posterior incompleto ou incorreto.')],**kw)


@pytest.mark.parametrize('state,level,expected', [('met',None,'4'),('partial','initial','2'),('not_met',None,'0'),('review',None,None),('error',None,None)])
def test_approved_levels_and_abstention(setup,monkeypatch,state,level,expected):
    _,_,run,review,rec,_=flow(setup,monkeypatch,[partial()],{'work':opinion(state,level)})
    assert rec['reconciled_suggested_score']==expected
    assert run.result.score==(float(expected) if expected is not None else None)
    if state=='partial':
        assert run.result.decisions[0].sufficiency=='PARTIAL'
        assert review['phase_a']['criterion_reviews'][0]['sufficiency']=='PARTIAL'
        assert rec['criteria'][0]['status']=='AGREEMENT_UNVERIFIED'
        assert run.result.analysis.provenance['semantic_evaluations'][0]['level_id']=='initial'
        assert not run.result.analysis.provenance['llm_used']
    if state=='error':assert rec['technical_uncertainty']


def test_lagrange_correct_setup_invalid_algebra_and_unsupported_answer(setup,monkeypatch):
    cs=[criterion('method','.4',1),criterion('system','.6',2),partial('algebra','.6',3),criterion('conclusion','.4',4)]
    cs[2]['credit_levels'][0]['description']='Deduzir x²=y² corretamente e excluir λ=0; a resolução posterior dos candidatos permanece incompleta ou errada.'
    g={'method':'met','system':'met','algebra':opinion('partial','initial',finding='MATHEMATICAL_ERROR'),'conclusion':'not_met'}
    _,_,run,_,rec,_=flow(setup,monkeypatch,cs,g)
    assert [d.sufficiency for d in run.result.decisions]==['COMPLETE','COMPLETE','PARTIAL','NOT_SATISFIED']
    # Derive expected from the approved levels; no reference score is an input.
    expected=sum(Decimal(cs[i]['max_points']) for i in (0,1))+Decimal(cs[2]['credit_levels'][0]['points'])
    assert Decimal(rec['reconciled_suggested_score'])==expected


@pytest.mark.parametrize('statement,solution,state,expected',[
 ('Simplifique (x²-1)/(x-1), indicando o domínio.','Fatoro x²-1=(x-1)(x+1); cancelo x-1 e obtenho x+1.','partial','2'),
 ('Calcule integral de x cos(x) e justifique.','Por partes u=x e dv=cos(x)dx. Obtenho x sen(x), mas não calculo a integral restante.','partial','2'),
 ('Determine o domínio de log(x-2) e justifique.','Exijo x-2>0; logo x>2, domínio (2,+infinito).','met','4')])
def test_unseen_algebra_integral_functions(setup,monkeypatch,statement,solution,state,expected):
    _,_,run,_,rec,calls=flow(setup,monkeypatch,[partial()],{'work':opinion(state,'initial' if state=='partial' else None)},statement=statement,solution=solution)
    assert rec['reconciled_suggested_score']==expected
    assert all(r['solution']==solution and 'reference_score' not in r for r in calls)
    assert run.result.decisions[0].semantic_trace['formal_certification'] is False


@pytest.mark.parametrize('selected',[
 opinion('partial','invented'),{**opinion('partial','initial'),'quotes':[]},
 {**opinion('met'),'quotes':['invented evidence']},opinion('not_met',finding='ABSENT_EVIDENCE'),opinion('met',finding='MATHEMATICAL_ERROR')])
def test_no_unauthorized_credit_or_missing_evidence(setup,monkeypatch,selected):
    _,_,run,_,rec,_=flow(setup,monkeypatch,[partial()],{'work':selected})
    assert run.result.score is None and rec['reconciled_suggested_score'] is None


def test_no_partial_when_rubric_has_no_levels(setup,monkeypatch):
    _,_,run,_,rec,_=flow(setup,monkeypatch,[criterion('work',4,1)],{'work':opinion('partial','initial')})
    assert run.result.score is None and rec['reconciled_suggested_score'] is None


@pytest.mark.parametrize('reviewer',[opinion('met'),opinion('not_met'),opinion('review')])
def test_partial_is_not_full_or_zero_agreement(setup,monkeypatch,reviewer):
    _,_,run,_,rec,_=flow(setup,monkeypatch,[partial()],{'work':opinion('partial','initial')},{'work':reviewer})
    assert run.result.score==2 and rec['reconciled_suggested_score'] is None
    assert rec['criteria'][0]['status']=='REVIEW_REQUIRED'


def dependent(kind=None):
    kw=dict(dependencies=['initial'])
    if kind:kw['dependency_rules']=[dict(criterion_id='initial',kind=kind,condition='Aplicar a condição explicitamente aprovada, preservando a etapa posterior independente quando cabível.')]
    return [partial('initial',4),partial('later',6,2,**kw)]


@pytest.mark.parametrize('kind,first,dep,expected',[
 ('MATHEMATICAL','met','satisfied','10'),('MATHEMATICAL','not_met','satisfied',None),
 ('MATHEMATICAL','review','satisfied',None),('MATHEMATICAL','met','unknown',None),
 ('PROCEDURAL','not_met','satisfied','6'),('PROCEDURAL','met','violated',None),
 ('CARRY_FORWARD','not_met','satisfied','6'),('CARRY_FORWARD','not_met','unknown',None),
 (None,'met','satisfied',None)])
def test_dependency_semantics_after_both_evaluators(setup,monkeypatch,kind,first,dep,expected):
    _,_,run,review,rec,_=flow(setup,monkeypatch,dependent(kind),{'initial':opinion(first),'later':opinion(dependency=dep)})
    assert rec['reconciled_suggested_score']==expected
    if expected is None:
        assert run.result.score is None
        assert run.result.decisions[1].dependency_trace['status'] in {'unknown','violated'}
        assert review['phase_a']['semantic_reviews']['later']['decision']=='review'


def test_upstream_disagreement_propagates_at_reconciliation_only(setup,monkeypatch):
    cs=dependent('MATHEMATICAL');cs[1]['dependency_rules'][0]['minimum_points']='2'
    _,_,run,review,rec,_=flow(setup,monkeypatch,cs,{'initial':'met','later':'met'}, {'initial':opinion('partial','initial'),'later':'met'})
    assert run.result.score==10
    assert review['phase_a']['criterion_reviews'][1]['proposed_points']=='6'
    assert all(r['status']=='REVIEW_REQUIRED' for r in rec['criteria'])
    assert 'Dependência' in rec['criteria'][1]['reason']


def test_dependency_order_is_graph_not_display_order():
    cs=dependent('MATHEMATICAL');cs=[dict(cs[1],order=1),dict(cs[0],order=2)]
    rubric=RubricContent(max_score='10',criteria=cs)
    snap={c['criterion_id']:dict(points=Decimal(c['max_points']),conclusive=True,sufficiency='COMPLETE',exact=True) for c in cs}
    assert assess_dependencies(rubric,snap)['later']['status']=='satisfied'


@pytest.mark.parametrize('bad',[dict(credit_levels=[dict(level_id='bad',points='4',description='exceeds partial')]),
 dict(dependencies=['missing']),dict(dependency_rules=[dict(criterion_id='missing',kind='MATHEMATICAL',condition='required')])])
def test_invalid_rubric_extensions_rejected(bad):
    with pytest.raises(ValueError):RubricContent(max_score='4',criteria=[criterion('work',4,1,**bad)])


def test_historical_rubric_serialization_unchanged():
    old=criterion('work',4,1)
    parsed=RubricCriterion(**old)
    assert 'credit_levels' not in parsed.model_dump() and 'dependency_rules' not in parsed.model_dump()
    wire=parsed.model_dump(mode='json');assert RubricCriterion.model_validate(wire).model_dump(mode='json')==wire


def test_exact_partial_credit_survives_semantic_provider_disagreement(setup,monkeypatch):
    from test_dynamic_semantic_consistency import roots_problem
    _,client=setup;monkeypatch.setenv('CONFIA_DYNAMIC_POLICY',DYNAMIC_VERSION)
    calls=simulated(monkeypatch,{}, {'roots':opinion('met'),'explanation':opinion('met')})
    doc=roots_problem(extra_semantic=True)
    # Existing exact roots coverage produces 3/6. No problem-specific checker is added.
    case,base,body=attempt(client,doc,'x=2')
    r=client.post(base+'/audits',json=body);assert r.status_code==200,r.text
    run=service().get(r.json()['audit_run_id']);root=run.result.decisions[0]
    assert root.suggested_points==3 and root.sufficiency=='PARTIAL' and root.semantic_trace is None
    assert all(r['criterion']['criterion_id']!='roots' for r in calls if r['stage']=='grader')
    prior=run.result.analysis.provenance['deterministic_pass']['decisions'][0]
    assert Decimal(prior['suggested_points'])==root.suggested_points


def test_partial_pending_adjudication_and_immutable_artifacts(setup,monkeypatch):
    client,case,run,review,rec,_=flow(setup,monkeypatch,[partial()],{'work':opinion('partial','initial')},{'work':'met'})
    before={p:p.read_bytes() for p in service().root.rglob('*.json')}
    body=dict(audit_run_id=run.audit_run_id,reconciliation_id=rec['reconciliation_id'],max_points='4',final_points='2',
        override_reason='Professor conferiu a etapa inicial prevista.',adjudication=dict(rubric_sha256=rec['context']['rubric_sha256'],criteria=[dict(criterion_id='work',final_points='2',justification='Etapa inicial válida conforme nível aprovado.')]))
    r=client.post(f"/tme/cases/{case['case_id']}/decision",json=body);assert r.status_code==201,r.text
    assert r.json()['suggested_points'] is None and Decimal(r.json()['final_points'])==2
    assert all(p.read_bytes()==raw for p,raw in before.items())
    persisted=service().get(run.audit_run_id)
    assert persisted.result.decisions[0].semantic_trace['level_id']=='initial'


@pytest.mark.parametrize('points',['1','3'])
def test_human_cannot_invent_new_discrete_level(setup,monkeypatch,points):
    client,case,run,_,rec,_=flow(setup,monkeypatch,[partial()],{'work':'review'})
    body=dict(audit_run_id=run.audit_run_id,reconciliation_id=rec['reconciliation_id'],max_points='4',final_points=points,
        override_reason='Justificativa explícita.',adjudication=dict(rubric_sha256=rec['context']['rubric_sha256'],criteria=[dict(criterion_id='work',final_points=points,justification='Crédito não autorizado.')]))
    assert client.post(f"/tme/cases/{case['case_id']}/decision",json=body).status_code==422


def test_semantic_contract_never_calls_unconfigured_provider(monkeypatch):
    import openai
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.setattr(openai,'OpenAI',lambda **kw:pytest.fail('network client constructed'))
    from confia_lean_auditor.dynamic.semantic_provenance import assess_with_provenance
    trace=assess_with_provenance(dict(stage='grader',solution=WORK,criterion=partial(),credit_contract='dynamic-credit.v1'))
    assert trace['decision']=='review' and trace['execution']['llm_used'] is False


def test_extended_provider_wire_contract_is_dynamic_only(monkeypatch):
    from confia_lean_auditor.dynamic.semantic_credit import SCHEMA
    from confia_lean_auditor.semantic_policy.minimal_review import SCHEMA as SHARED
    import openai
    monkeypatch.setenv('CONFIA_SEMANTIC_LLM_ENABLED','1');monkeypatch.setenv('OPENAI_API_KEY','simulated-not-a-secret')
    calls=[]
    class Client:
        def __init__(self,**kw):self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kw):
            calls.append(kw);return SimpleNamespace(status='completed',id='mock',model='simulated',usage=None,output_text=json.dumps(dict(decision='partial',level_id='initial',justification='Etapa válida.',quotes=[WORK],finding='INCOMPLETE_DEVELOPMENT',dependencies=[])))
    monkeypatch.setattr(openai,'OpenAI',Client)
    response=DynamicCreditProvider()(dict(solution=WORK,criterion=partial()))
    assert response['decision']=='partial' and calls[0]['text']['format']['schema']==SCHEMA
    assert SHARED['properties']['decision']['enum']==['met','not_met','review']
    assert 'partial' not in SHARED['properties']['decision']['enum']


@pytest.mark.parametrize('response',[None,[], 'invalid', {'decision':'partial'}, {'decision':'partial','level_id':'initial','justification':'','quotes':[WORK],'finding':'VALID_ARGUMENT','dependencies':[]}])
def test_malformed_provider_response_remains_pending(response):
    from confia_lean_auditor.dynamic.semantic_provenance import assess_with_provenance
    trace=assess_with_provenance(dict(stage='grader',solution=WORK,criterion=partial(),credit_contract='dynamic-credit.v1'),lambda _:response)
    assert trace['decision']=='review'
    assert not trace.get('response') or isinstance(trace['response'],dict)


def test_human_mathematical_dependency_cannot_be_bypassed(setup,monkeypatch):
    client,case,run,_,rec,_=flow(setup,monkeypatch,dependent('MATHEMATICAL'),{'initial':'not_met','later':'met'})
    body=dict(audit_run_id=run.audit_run_id,reconciliation_id=rec['reconciliation_id'],max_points='10',final_points='6',override_reason='Adjudicação docente.',
        adjudication=dict(rubric_sha256=rec['context']['rubric_sha256'],criteria=[dict(criterion_id='initial',final_points='0',justification='Erro matemático.'),
        dict(criterion_id='later',final_points='6',justification='Etapa posterior.',dependency_justification='Tentativa de ignorar o requisito matemático.')] ))
    assert client.post(f"/tme/cases/{case['case_id']}/decision",json=body).status_code==422


def test_lagrange_invalid_work_does_not_earn_credit_for_only_a_correct_answer(setup,monkeypatch):
    # The simulated provider rejects the justification; the integration must not
    # replace that decision with final-answer string matching.
    _,_,run,_,rec,_=flow(setup,monkeypatch,[partial('proof',2)],{'proof':opinion('not_met',finding='MATHEMATICAL_ERROR')},solution='Digo que x=2y sem justificar. A resposta final é 1/2.')
    assert rec['reconciled_suggested_score']=='0'
    assert run.result.decisions[0].semantic_trace['finding']=='MATHEMATICAL_ERROR'
