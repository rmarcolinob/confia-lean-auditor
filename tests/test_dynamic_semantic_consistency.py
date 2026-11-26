"""Current-policy regressions. Providers/metadata are explicitly simulated, never paid."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_dynamic_dy3 import setup, attempt, ACTOR
from test_dec10_integration import teacher_problem, SOLUTION
from confia_lean_auditor.dynamic.models import CreateProblem, SaveRubric, ApproveRubric
from confia_lean_auditor.dynamic.store import dynamic_store
from confia_lean_auditor.dynamic.grading_context import resolve
from confia_lean_auditor.dynamic.review_models import DynamicIndependentReview
from confia_lean_auditor.dynamic.reconciliation_models import DynamicReconciliation
from confia_lean_auditor.dynamic.semantic import reconcile
from confia_lean_auditor.dynamic.semantic_provenance import assess_with_provenance
from confia_lean_auditor.semantic_policy.service import SemanticProvider, DYNAMIC_VERSION
from confia_lean_auditor.submissions.integrity import canonical_sha256, model_sha256


@pytest.fixture
def current_policy(monkeypatch):
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY', DYNAMIC_VERSION)


def provider_stub(monkeypatch, grader='met', reviewer='met', metadata=True):
    calls=[]
    def call(self, request):
        calls.append(deepcopy(request))
        decision=reviewer if request['stage']=='independent_reviewer' else grader
        if decision=='error':
            raise TimeoutError('simulated offline timeout')
        if metadata:
            self.metadata=dict(provider='controlled-test',model='fixture-model',requested_model='fixture-model',
                response_id='simulated-'+str(len(calls)),llm_used=False)
        return dict(decision=decision,justification='Parecer simulado por critério, não prova formal.',quotes=[request['solution']])
    monkeypatch.setattr(SemanticProvider,'__call__',call)
    return calls


def roots_problem(extra_semantic=False):
    store=dynamic_store()
    doc=store.create(CreateProblem(statement='Resolva nos reais: x²-5x+6=0.',max_score='10',correction_mode='DYNAMIC'),ACTOR)
    pid=doc['problem']['problem_id']
    criteria=[dict(criterion_id='roots',title='Raízes',description='Obter todas as raízes reais. Crédito parcial proporcional às raízes corretas.',max_points='6' if extra_semantic else '10',order=1)]
    if extra_semantic:
        criteria.append(dict(criterion_id='explanation',title='Explicação',description='Explicar por que essas soluções atendem ao problema.',max_points='4',order=2))
    doc=store.save_rubric(pid,SaveRubric(expected_revision=doc['revision'],statement_version=1,max_score='10',criteria=criteria),ACTOR)
    return store.approve(pid,doc['rubrics'][-1]['rubric_id'],ApproveRubric(expected_revision=doc['revision']),ACTOR)


def audit(client,doc,text):
    case,base,body=attempt(client,doc,text)
    response=client.post(base+'/audits',json=body)
    assert response.status_code==200,response.text
    return case,base,body,response.json()


def review_and_reconcile(client,case,run,profile='FORMATIVE_LIST'):
    prefix=f"/dynamic/attempts/{case['case_id']}"
    response=client.post(prefix+'/policy',json={'policy_profile':profile})
    assert response.status_code==201,response.text
    url=prefix+'/audits/'+run['audit_run_id']
    response=client.post(url+'/independent-reviews',json={'execution_key':'semantic-consistency'})
    assert response.status_code==201,response.text
    review=response.json()['review']
    response=client.post(url+'/reconciliations',json={'independent_review_id':review['review_id']})
    assert response.status_code==201,response.text
    rec=response.json()['reconciliation']
    assert client.get(url+'/independent-reviews').json()[0]['review']==review
    assert client.get(url+'/reconciliations').json()[0]['reconciliation']==rec
    return review,rec


@pytest.mark.parametrize('profile',['FORMATIVE_LIST','SCHOOL_EXAM'])
@pytest.mark.parametrize('reviewer',['met','not_met'])
def test_exact_partial_credit_is_neither_full_nor_zero(setup,current_policy,monkeypatch,profile,reviewer):
    _,client=setup;calls=provider_stub(monkeypatch,reviewer=reviewer)
    case,base,body,run=audit(client,roots_problem(),'x=2')
    original=deepcopy(run)
    assert run['result']['score']==5
    assert calls==[] # exact partial result never sent to the Grader fallback
    review,rec=review_and_reconcile(client,case,run,profile)
    row=rec['criteria'][0]
    assert row['grader_points']==row['reconciled_points']=='5.00'
    assert row['reviewer_points']==('10' if reviewer=='met' else '0')
    assert row['status']=='REVIEW_REQUIRED' and row['automation']=='REVIEW_ONLY'
    assert 'Divergência numérica' in row['reason']
    assert rec['reconciled_suggested_score'] is None and not rec['technical_uncertainty']
    assert review['comparison']['status']=='DISAGREEMENT'
    assert any(e['event_type']=='grader_reviewer_disagreement' for e in review['events'])
    assert not any(e['event_type']=='criterion_auto_accepted' for e in rec['events'])
    assert client.post(base+'/audits',json=body).json()==original
    assert len(calls)==1


@pytest.mark.parametrize('text,reviewer,score', [('S={2,3}','met',10),('x=9','not_met',0)])
def test_exact_agreement_preserves_verified_decision_without_grader_llm(setup,current_policy,monkeypatch,text,reviewer,score):
    _,client=setup;calls=provider_stub(monkeypatch,reviewer=reviewer)
    case,_,_,run=audit(client,roots_problem(),text)
    assert run['result']['score']==score and calls==[]
    assert run['result']['analysis']['provenance']['llm_used'] is False
    assert 'deterministic_pass' not in run['result']['analysis']['provenance']
    review,rec=review_and_reconcile(client,case,run)
    assert rec['criteria'][0]['status']=='AGREEMENT_SUPPORTED'
    assert rec['criteria'][0]['automation']=='AUTO_ACCEPT'
    assert Decimal(rec['reconciled_suggested_score'])==score
    assert review['comparison']['status']=='AGREEMENT'


@pytest.mark.parametrize('grader,reviewer,score,technical',[
    ('met','met','10',False),('not_met','not_met','0',False),
    ('met','not_met',None,False),('not_met','met',None,False),
    ('review','met',None,False),('error','met',None,True),
    ('met','review',None,False),('met','error',None,True)])
def test_current_policy_decisions_projections_and_persisted_evidence(setup,current_policy,monkeypatch,grader,reviewer,score,technical):
    _,client=setup;calls=provider_stub(monkeypatch,grader,reviewer)
    case,base,body,run=audit(client,teacher_problem(),SOLUTION)
    result=run['result'];provenance=result['analysis']['provenance']
    previous=provenance['deterministic_pass']
    assert previous['provenance']['llm_used'] is False
    assert previous['reviewed_components']==[] and previous['unreviewed_components']==['area','unit']
    assert all(d['automation']=='REVIEW_ONLY' for d in previous['decisions'])
    assert provenance['semantic_evaluation_attempted']
    assert 'resíduo semântico não executados' not in provenance['selection_reason']
    assert result['reviewed_components']==(['area','unit'] if grader in {'met','not_met'} else [])
    assert result['unreviewed_components']==([] if grader in {'met','not_met'} else ['area','unit'])
    events=[e for e in result['events'] if e['event_type']=='dynamic_semantic_rubric_decision']
    assert len(events)==2 and len({e['event_id'] for e in result['events']})==len(result['events'])
    assert [e['event_id'] for e in result['events'][:len(previous['event_ids'])]]==previous['event_ids']
    assert result['events'][-1]['score']==result['score']
    if grader!='error':
        assert provenance['model']=='fixture-model' and provenance['provider']=='controlled-test'
        assert provenance['llm_used'] is False # explicit simulation metadata, not a real LLM
        claim_map={c['claim_id']:c for c in result['analysis']['claims']}
        for d,event in zip(result['decisions'],events):
            assert event['justification']==d['explanation']
            for cid in d['claim_ids']:
                claim=claim_map[cid]
                assert SOLUTION[claim['start']:claim['end']]==claim['text']
                assert any(b['claim_id']==cid and b['criterion_id']==d['criterion_id'] for b in result['bindings'])
    else:
        assert provenance['model'] is None and provenance['llm_used'] is None
    review,rec=review_and_reconcile(client,case,run)
    assert rec['reconciled_suggested_score']==score and rec['technical_uncertainty']==technical
    assert review['context_snapshot']['provider_adapter']=='SemanticProvider'
    assert len([e for e in review['events'] if e['event_type']=='independent_semantic_criterion_review'])==2
    if score is not None:
        assert {r['status'] for r in rec['criteria']}=={'AGREEMENT_UNVERIFIED'}
        assert review['comparison']['status']=='AGREEMENT' and review['review_required']
    assert all(r['automation']=='REVIEW_ONLY' for r in rec['criteria'])
    assert client.post(base+'/audits',json=body).json()==run
    assert len(calls)==4
    from confia_lean_auditor.submission_audits.router import service
    saved=service().get(run['audit_run_id']).result.model_dump(mode='json')
    assert {**saved,'artifact_dir':None}==result # the public API deliberately redacts local paths
    stored=Path(saved['artifact_dir'])
    assert json.loads((stored/'analysis.json').read_text())==result['analysis']
    assert json.loads((stored/'audit.json').read_text())==saved


def test_unknown_provider_metadata_stays_unknown(setup,current_policy,monkeypatch):
    _,client=setup;provider_stub(monkeypatch,metadata=False)
    _,_,_,run=audit(client,teacher_problem(),SOLUTION)
    p=run['result']['analysis']['provenance']
    assert p['llm_used'] is None and p['model'] is None and p['provider'] is None
    assert all(e['execution']['response_received'] for e in p['semantic_evaluations'])


def test_disabled_provider_is_not_llm_use_or_mathematical_zero(setup,current_policy,monkeypatch):
    import openai
    monkeypatch.setattr(openai,'OpenAI',lambda **_:pytest.fail('network client constructed'))
    _,client=setup
    _,_,_,run=audit(client,teacher_problem(),SOLUTION)
    result=run['result'];p=result['analysis']['provenance']
    assert result['score'] is None and result['verdict']=='falha_tecnica'
    assert p['llm_used'] is False and p['model'] is None
    assert all(e['execution']['state']=='unavailable' for e in p['semantic_evaluations'])


def test_actual_adapter_receipt_populates_known_llm_metadata_offline(setup,current_policy,monkeypatch):
    import openai
    calls=[]
    class FakeClient:
        def __init__(self,**kwargs):self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kwargs):
            calls.append(kwargs)
            request=json.loads(kwargs['input'][1]['content'])
            return SimpleNamespace(id='simulated-response-'+str(len(calls)),model='simulated-returned-model',status='completed',usage=None,
                output_text=json.dumps(dict(decision='met',justification='Resposta do SDK simulado; nenhuma API real.',quotes=[request['solution']])))
    monkeypatch.setenv('CONFIA_SEMANTIC_LLM_ENABLED','1')
    monkeypatch.setenv('OPENAI_API_KEY','offline-placeholder-not-a-credential')
    monkeypatch.setenv('CONFIA_SEMANTIC_MODEL','simulated-requested-model')
    monkeypatch.setattr(openai,'OpenAI',FakeClient)
    _,client=setup
    case,_,_,run=audit(client,teacher_problem(),SOLUTION)
    p=run['result']['analysis']['provenance']
    assert p['llm_used'] is True and p['provider']=='openai'
    assert p['model']=='simulated-returned-model' and p['requested_model']=='simulated-requested-model'
    review,_=review_and_reconcile(client,case,run)
    rp=review['phase_a']['provenance']
    assert rp['provider']=='openai' and rp['returned_model']=='simulated-returned-model'
    assert rp['requested_model']=='simulated-requested-model' and len(calls)==4


def test_reused_provider_timeout_does_not_inherit_previous_receipt():
    class Reused:
        metadata=None
        def __call__(self,request):
            if self.metadata:raise TimeoutError('offline failure')
            self.metadata=dict(provider='controlled-test',model='fixture',response_id='first-only',llm_used=False)
            return dict(decision='met',justification='Controlled response',quotes=['written'])
    provider=Reused();request=dict(stage='grader',solution='written')
    first=assess_with_provenance(request,provider);second=assess_with_provenance(request,provider)
    assert first['execution']['response_id']=='first-only'
    assert second['execution']['response_id'] is None and second['execution']['model'] is None
    assert second['execution']['llm_used'] is None and second['decision']=='review'


@pytest.mark.parametrize('mutation',['same_points_wrong_state','wrong_maximum','missing_criterion','technical_met','unsupported_partial'])
def test_numerical_equality_alone_cannot_auto_accept(setup,current_policy,monkeypatch,mutation):
    _,client=setup;provider_stub(monkeypatch)
    doc=roots_problem();case,_,_,run=audit(client,doc,'S={2,3}')
    review,_=review_and_reconcile(client,case,run)
    from confia_lean_auditor.submission_audits.router import service
    g=service().get(run['audit_run_id']).result;r=DynamicIndependentReview.model_validate(review)
    criterion=r.phase_a.criterion_reviews[0]
    if mutation=='same_points_wrong_state':criterion=criterion.model_copy(update={'sufficiency':'NOT_SATISFIED'})
    elif mutation=='wrong_maximum':criterion=criterion.model_copy(update={'max_points':Decimal('20')})
    elif mutation=='missing_criterion':criterion=None
    elif mutation=='technical_met':r.phase_a.semantic_reviews['roots']['error_type']='TimeoutError'
    else:
        g=g.model_copy(update=dict(score=5,suggested_score=5,decisions=[g.decisions[0].model_copy(update=dict(suggested_points=Decimal('5'),sufficiency='PARTIAL'))]))
        criterion=criterion.model_copy(update=dict(proposed_points=Decimal('5'),sufficiency='PARTIAL',assessment='PARTIAL'))
    r=r.model_copy(update={'phase_a':r.phase_a.model_copy(update={'criterion_reviews':[criterion] if criterion else []})})
    rubric=resolve(doc['problem']['problem_id'],ACTOR)[2]
    row=reconcile(g,r,rubric)[0]
    assert row.status in {'REVIEW_REQUIRED','TECHNICAL_ERROR'} and row.automation=='REVIEW_ONLY'
    assert row.reconciled_points==g.decisions[0].suggested_points


def test_mixed_exact_and_semantic_pass_preserves_exact_decision_and_event(setup,current_policy,monkeypatch):
    _,client=setup;calls=provider_stub(monkeypatch)
    _,_,_,run=audit(client,roots_problem(extra_semantic=True),'S={2,3}; ambos anulam o polinômio.')
    r=run['result'];previous=r['analysis']['provenance']['deterministic_pass']
    assert r['score']==10 and r['reviewed_components']==['roots','explanation']
    assert r['decisions'][0]==previous['decisions'][0]
    assert r['decisions'][0]['suggested_points']=='6'
    assert [c['criterion']['criterion_id'] for c in calls]==['explanation']
    initial_event=next(e for e in r['events'] if e['event_type']=='dynamic_rubric_decision' and e['criterion_id']=='roots')
    assert initial_event['suggested_points']=='6' and initial_event['event_id'] in previous['event_ids']


def test_exact_conflict_is_not_overwritten_by_positive_semantic_reply(setup,current_policy,monkeypatch):
    _,client=setup;provider_stub(monkeypatch)
    _,_,_,run=audit(client,roots_problem(),'S={2,3}; S={2,9}')
    result=run['result'];trace=result['decisions'][0]['semantic_trace']
    assert trace['response']['decision']=='met' and trace['decision']=='review'
    assert trace['gate_reason']=='EXACT_CONFLICT_REQUIRES_REVIEW'
    assert result['score'] is None and result['unreviewed_components']==['roots']
    assert result['analysis']['provenance']['semantic_evaluations'][0]['gate_reason']==trace['gate_reason']


def test_archived_legacy_records_keep_serialized_hashes():
    root=Path(__file__).resolve().parents[1]/'docs/audits/assets/confia-dynamic-dy5/records/audits'
    count=0
    for folder,key,model in [('reconciliations','data',DynamicReconciliation),('independent_reviews','record',DynamicIndependentReview)]:
        for path in (root/folder).glob('*.json'):
            before=path.read_bytes();raw=json.loads(before)
            restored=model.model_validate(raw[key])
            assert model_sha256(restored)==raw['sha256']==canonical_sha256(raw[key])
            assert path.read_bytes()==before
            count+=1
    assert count==12
