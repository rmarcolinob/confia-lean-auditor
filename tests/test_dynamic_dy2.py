"""Controlled providers only: mathematical scope, lifecycle, races, provenance/auth."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from fractions import Fraction
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from pydantic import ValidationError
from confia_lean_auditor.dynamic.models import (CreateStatement, PreparationRequest, SuggestionRequest,
    ApproveRubric, SaveRubric, SuggestedRubric, model_sha256)
from confia_lean_auditor.dynamic.preparation_models import (PreparationProposal, SemanticReview,
    GenerationProvenance, CheckSpec)
from confia_lean_auditor.dynamic.preparation import PreparationService
from confia_lean_auditor.dynamic.provider import ProviderFailure, OpenAIPreparationProvider
from confia_lean_auditor.dynamic.verification import analyze, polynomial, root_set
from confia_lean_auditor.dynamic.store import DynamicStore, DynamicConflict
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.assessments.store import AssessmentIntegrityConflict
from test_dynamic_dy1 import ACTOR, CRITERIA, create, store, api, api_create
from test_core_auth import auth_case


def proposal():
    return dict(mathematical_domain='Álgebra real', normalized_problem='Resolver a equação em R.',
        data=['x² - 5x + 6 = 0'], assumptions=[], objects=[dict(name='x',domain='R',constraints=[])],
        target='Conjunto completo de raízes.',expects_unique_result=False,
        candidate_reference_solutions=[dict(solution_id='s1',strategy_id='factor',strategy_label='Fatoração',
            claims=[dict(claim_id='factorization',text='x² - 5x + 6 = (x-2)(x-3)',normalized_form='x^2-5*x+6=(x-2)*(x-3)',
                claim_type='identity',dependencies=[],mathematical_objects=['x'],proposed_verifier='SYMBOLIC_ALGEBRA',
                verifier_reason='Identidade polinomial',formalizability_candidate=True,
                check=dict(kind='EQUALITY',left='x^2-5*x+6',right='(x-2)*(x-3)',variable='x',values=[])),
                dict(claim_id='roots',text='As raízes são 2 e 3.',normalized_form='S={2,3}',claim_type='root_set',
                dependencies=['factorization'],mathematical_objects=['x'],proposed_verifier='DETERMINISTIC',
                verifier_reason='Divisão exata comprova todas as raízes',formalizability_candidate=True,
                check=dict(kind='ROOT_SET',left='x^2-5*x+6',right='0',variable='x',values=['2','3']))],
            final_result=dict(kind='ROOT_SET',text='{2,3}',values=['2','3'],supporting_claim_ids=['roots']),uncertainties=[])],
        alternative_strategies=[dict(strategy_id='factor',description='Fatoração ou produto nulo',expected_key_claim_ids=['factorization','roots']),
            dict(strategy_id='formula',description='Fórmula quadrática também é legítima.',expected_key_claim_ids=['roots'])],warnings=[],uncertainties=[])


def suggestion():
    criteria=deepcopy(CRITERIA)
    for c in criteria:
        c['evidence']=dict(mathematical_objective=c['description'],related_reference_claims=['roots'],
            accepted_alternative_strategies=['factor','formula'],verifier_hints=['DETERMINISTIC'],warnings=[])
    return dict(max_score='10',criteria=criteria,warnings=[])


class ControlledProvider:
    def __init__(self, preparation=None, rubric=None, review=None, failure=None):
        self.preparation=preparation or proposal(); self.rubric=rubric or suggestion()
        self.review=review or dict(warnings=[],overlap_detected=False,vague_criteria=False,
            impossible_dependency=False,absent_information_required=False,unjustified_single_strategy=False,rationale='Critérios distintos e métodos equivalentes aceitos.')
        self.failure=failure; self.calls=[]
    def generate(self, operation, payload, response_type):
        self.calls.append((operation,payload))
        if self.failure == operation: raise ProviderFailure('CONTROLLED_FAILURE')
        raw={'prepare':self.preparation,'rubric':self.rubric,'review_rubric':self.review}[operation]
        output=response_type.model_validate(raw)
        return output, GenerationProvenance(provider='controlled-test',requested_model='fixture',returned_model='fixture-v1',
            reasoning_effort=None,prompt_version='test:'+operation,schema_version=response_type.__name__+'.v1',
            input_sha256=canonical_sha256(payload),output_sha256=canonical_sha256(json.dumps(raw)),response_id=None,
            created_at=datetime.now(timezone.utc),code_sha=None,max_output_tokens=10000,raw_output=json.dumps(raw))


def prepare(store, doc=None, provider=None):
    doc=doc or create(store)
    return PreparationService(store,provider or ControlledProvider()).start(doc['problem']['problem_id'],
        PreparationRequest(expected_revision=doc['revision']),ACTOR)


def suggest(store,doc,provider=None,reason=None):
    return PreparationService(store,provider or ControlledProvider()).suggest(doc['problem']['problem_id'],
        SuggestionRequest(expected_revision=doc['revision'],preparation_id=doc['current_preparation']['preparation_id'],reason=reason),ACTOR)


def approve(store,doc,ack=False):
    return store.approve(doc['problem']['problem_id'],doc['rubrics'][-1]['rubric_id'],
        ApproveRubric(expected_revision=doc['revision'],acknowledge_warnings=ack),ACTOR)


def test_preparation_stages_exact_checks_binding_provenance_and_no_autoapproval(store):
    provider=ControlledProvider();doc=prepare(store,provider=provider)
    assert [p['status'] for p in doc['preparations']]==['PENDING','RUNNING','READY_FOR_REVIEW']
    prep=doc['current_preparation'];assert prep['statement_version']==1
    assert prep['proposal']['candidate_reference_solutions'][0]['final_result']['values']==['2','3']
    assert len(prep['proposal']['alternative_strategies'])==2
    assert {c['status'] for c in prep['analysis']['verifier_plan']}=={'VERIFIED_WITHIN_SCOPE'}
    assert {c['formal_status'] for c in prep['analysis']['verifier_plan']}=={'FORMAL_NOT_ATTEMPTED'}
    assert not prep['analysis']['automatic_correction_allowed']
    assert prep['provenance']['input_sha256']==canonical_sha256(provider.calls[0][1])
    assert prep['provenance']['output_sha256']==canonical_sha256(prep['provenance']['raw_output'])
    assert doc['packages'][-1]['preparation_reference']['preparation_id']==prep['preparation_id']
    assert not doc['approvals'] and doc['current_configuration'] is None
    assert DynamicStore(store.root).get(doc['problem']['problem_id'],ACTOR)==doc


def test_ai_suggestion_regeneration_edit_and_explicit_approval(store):
    doc=suggest(store,prepare(store));first=deepcopy(doc['rubrics'][-1])
    assert first['status']=='DRAFT_AI' and first['provenance']['origin']=='AI'
    assert not doc['approvals']
    doc=suggest(store,doc,reason='Rever a distribuição de pontos')
    assert len(doc['rubrics'])==2 and doc['rubrics'][0]==first
    assert doc['rubrics'][-1]['generation']['previous_rubric_id']==first['rubric_id']
    assert doc['rubrics'][-1]['generation']['reason']=='Rever a distribuição de pontos'
    criteria=deepcopy(doc['rubrics'][-1]['criteria']);criteria[0]['description']='Método equivalente justificado.'
    doc=store.save_rubric(doc['problem']['problem_id'],SaveRubric(expected_revision=doc['revision'],statement_version=1,
        max_score=10,criteria=criteria),ACTOR,base_id=doc['rubrics'][-1]['rubric_id'])
    assert doc['rubrics'][-1]['status']=='TEACHER_EDITED'
    assert doc['rubrics'][-1]['generation']['generation']['provider']=='controlled-test'
    doc=approve(store,doc)
    assert doc['rubrics'][-1]['status']=='APPROVED'
    assert doc['packages'][-1]['preparation_status']=='READY_FOR_REVIEW'
    assert doc['current_configuration']['package']['package_sha256']


def test_ambiguity_visible_and_acknowledgement_does_not_upgrade_trust(store):
    value=proposal();value['assumptions']=[dict(text='Lado não fornecido',source='INFERRED')]
    value['warnings']=[dict(code='MISSING_DATA',message='Falta uma medida.',requires_review=True)]
    doc=suggest(store,prepare(store,provider=ControlledProvider(preparation=value)))
    assert doc['current_preparation']['status']=='REVIEW_REQUIRED'
    with pytest.raises(DynamicConflict,match='avisos'):approve(store,doc)
    doc=approve(store,doc,True)
    assert doc['approvals'][-1]['acknowledged_warnings']
    assert doc['current_preparation']['analysis']['trust_state']=='HUMAN_REVIEW_REQUIRED'
    assert not doc['current_preparation']['analysis']['automatic_correction_allowed']


def test_statement_change_supersedes_preparation_and_derived_rubric(store):
    doc=approve(store,suggest(store,prepare(store)))
    files={p:p.read_bytes() for p in store.folder(doc['problem']['problem_id']).glob('*.json')}
    doc=store.statement(doc['problem']['problem_id'],CreateStatement(expected_revision=doc['revision'],statement='Resolva y² - 9 = 0',max_score=10),ACTOR)
    assert doc['current_preparation'] is None and doc['current_configuration'] is None
    assert doc['preparation_history'][0]['effective_status']=='SUPERSEDED'
    assert doc['rubrics'][0]['status']=='SUPERSEDED'
    assert all(p.read_bytes()==data for p,data in files.items())
    with pytest.raises(DynamicConflict):
        PreparationService(store,ControlledProvider()).suggest(doc['problem']['problem_id'],SuggestionRequest(expected_revision=doc['revision'],preparation_id=doc['preparation_history'][0]['preparation_id']),ACTOR)


def test_new_preparation_keeps_previous_history_and_blocks_old_draft_approval(store):
    doc=suggest(store,prepare(store));old=deepcopy(doc['preparations'])
    doc=prepare(store,doc)
    assert doc['preparations'][:len(old)]==old
    assert [p['effective_status'] for p in doc['preparation_history']]==['SUPERSEDED','READY_FOR_REVIEW']
    with pytest.raises(DynamicConflict):approve(store,doc)
    doc=suggest(store,doc)
    assert doc['rubrics'][-1]['preparation_reference']['preparation_version']==2


@pytest.mark.parametrize('mutation,code',[
    (lambda p:p['candidate_reference_solutions'][0]['claims'][0]['check'].update(right='(x-1)*(x-3)'), 'CONTRADICTED_CLAIM'),
    (lambda p:p['candidate_reference_solutions'][0]['final_result'].update(values=['2','4']), 'FINAL_RESULT_UNVERIFIED'),
    (lambda p:p.update(candidate_reference_solutions=[],alternative_strategies=[]), 'NO_CANDIDATE'),
    (lambda p:p.update(uncertainties=['Notação ambígua']), 'INTERPRETATION_UNCERTAIN'),
])
def test_consistency_errors_require_review(mutation,code):
    p=proposal();mutation(p);result=analyze(PreparationProposal.model_validate(p))
    assert result.trust_state=='HUMAN_REVIEW_REQUIRED'
    assert code in {w.code for w in result.warnings}


def test_incompatible_alternative_is_never_chosen_silently():
    p=proposal();other=deepcopy(p['candidate_reference_solutions'][0]);other['solution_id']='s2';other['strategy_id']='formula'
    for c in other['claims']:
        c['claim_id']='alt_'+c['claim_id'];c['dependencies']=['alt_'+d for d in c['dependencies']]
    other['final_result'].update(values=['1','5'],supporting_claim_ids=['alt_roots'])
    p['candidate_reference_solutions'].append(other)
    result=analyze(PreparationProposal.model_validate(p))
    assert 'INCOMPATIBLE_RESULTS' in {w.code for w in result.warnings}
    assert result.trust_state=='HUMAN_REVIEW_REQUIRED'


@pytest.mark.parametrize('capability',['NUMERICAL','FINITE_ENUMERATION','LEAN_CANDIDATE','SEMANTIC_RESIDUAL','REVIEW_ONLY'])
def test_unavailable_plan_is_not_a_verification(capability):
    p=proposal();p['candidate_reference_solutions'][0]['claims'][1]['proposed_verifier']=capability
    p['candidate_reference_solutions'][0]['claims'][1]['check']['kind']='NONE'
    result=analyze(PreparationProposal.model_validate(p));c=result.verifier_plan[1]
    assert not c.available and c.status=='UNVERIFIED' and c.formal_status=='FORMAL_NOT_ATTEMPTED'
    assert result.trust_state=='HUMAN_REVIEW_REQUIRED'


@pytest.mark.parametrize('text',['__import__("os").system("echo bad")','x^1000','1/(x-2)','sin(x)','x*y','(x+1)^13'])
def test_verifier_rejects_code_domain_changes_and_large_expansion(text):
    with pytest.raises(ValueError):polynomial(text,'x')


@pytest.mark.parametrize('left,roots,expected',[
    ('2*x^2-10*x+12',['2','3'],True),('x^2-9',['-3','3'],True),
    ('x^2-4*x+4',['2'],True),('x^2-5*x+6',['2'],False),
    ('x^2-5*x+6',['2','4'],False),('x^2-2',['1.414'],False),
    ('(x-1)*(x-2)*(x-3)',['1','2','3'],True)])
def test_generic_root_completeness_not_hardcoded(left,roots,expected):
    assert root_set(CheckSpec(kind='ROOT_SET',left=left,right='0',variable='x',values=roots)) is expected


def test_failure_persisted_and_recovery_creates_new_version(store,monkeypatch):
    monkeypatch.delenv('CONFIA_DYNAMIC_LLM_ENABLED',raising=False)
    doc=prepare(store,provider=OpenAIPreparationProvider())
    assert doc['current_preparation']['status']=='FAILED'
    assert doc['current_preparation']['failure_code']=='PROVIDER_NOT_CONFIGURED'
    assert not doc['rubrics'] and doc['current_configuration'] is None
    doc=prepare(store,doc)
    assert doc['current_preparation']['preparation_version']==2
    assert doc['preparation_history'][0]['effective_status']=='SUPERSEDED'


@pytest.mark.parametrize('mutation',[
    lambda r:r['criteria'][0].update(max_points=9),
    lambda r:r['criteria'][0].update(criterion_id='roots'),
    lambda r:r['criteria'][0]['evidence'].update(related_reference_claims=['missing']),
    lambda r:r['criteria'][0].update(order=7),
    lambda r:r.update(max_score=11),
])
def test_invalid_suggestion_never_publishes_rubric(store,mutation):
    doc=prepare(store);value=suggestion();mutation(value)
    with pytest.raises(ProviderFailure):suggest(store,doc,ControlledProvider(rubric=value))
    latest=store.get(doc['problem']['problem_id'],ACTOR)
    assert not latest['rubrics'] and not latest['approvals']
    assert latest['events'][-1]['event_type']=='rubric_suggestion_failed'


def test_structured_semantic_review_and_unverified_criterion_require_review(store):
    p=proposal();p['candidate_reference_solutions'][0]['claims'][1]['proposed_verifier']='REVIEW_ONLY'
    p['candidate_reference_solutions'][0]['claims'][1]['check']['kind']='NONE'
    doc=prepare(store,provider=ControlledProvider(preparation=p))
    provider=ControlledProvider();provider.review['unjustified_single_strategy']=True
    doc=suggest(store,doc,provider)
    codes={w['code'] for w in doc['rubrics'][-1]['review_warnings']}
    assert 'UNVERIFIED_CRITERION' in codes and 'SEMANTIC_UNJUSTIFIED_SINGLE_STRATEGY' in codes
    assert [op for op,_ in provider.calls]==['rubric','review_rubric']
    with pytest.raises(DynamicConflict):approve(store,doc)


def test_network_not_under_lock_and_late_result_never_applies_to_new_statement(store):
    started,release=Event(),Event();provider=ControlledProvider();original=provider.generate
    def wait(*args):started.set();assert release.wait(10);return original(*args)
    provider.generate=wait;doc=create(store);pid=doc['problem']['problem_id']
    with ThreadPoolExecutor() as pool:
        future=pool.submit(prepare,store,doc,provider);assert started.wait(10)
        latest=store.get(pid,ACTOR);assert latest['current_preparation']['status']=='RUNNING'
        with pytest.raises(DynamicConflict):prepare(store,latest)
        changed=store.statement(pid,CreateStatement(expected_revision=latest['revision'],statement='Novo enunciado',max_score=10),ACTOR)
        release.set();result=future.result(timeout=10)
    assert result['current_preparation'] is None and result['current_configuration'] is None
    assert result['preparation_history'][0]['effective_status']=='SUPERSEDED'
    assert result['packages'][-1]==changed['packages'][-1]


def test_api_authorization_preparation_and_ai_draft(api,monkeypatch):
    clients,_=api;client=clients('teacher.a');doc=api_create(client);pid=doc['problem']['problem_id'];prefix='/dynamic/problems/'+pid
    controlled=ControlledProvider()
    monkeypatch.setattr(OpenAIPreparationProvider,'generate',controlled.generate)
    monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','1');monkeypatch.setenv('OPENAI_API_KEY','unit-test-not-a-secret')
    assert clients('student.a').post(prefix+'/preparations',json={'expected_revision':1}).status_code==403
    assert clients('teacher.b').post(prefix+'/preparations',json={'expected_revision':1}).status_code==404
    response=client.post(prefix+'/preparations',json={'expected_revision':1});assert response.status_code==201,response.text
    doc=response.json();prep=doc['current_preparation']
    assert client.get(prefix+'/preparations').json()[0]['preparation_id']==prep['preparation_id']
    assert client.get(prefix+'/preparations/'+prep['preparation_id']).json()==prep
    response=client.post(prefix+'/rubric-suggestion',json=dict(expected_revision=doc['revision'],preparation_id=prep['preparation_id']))
    assert response.status_code==200,response.text
    doc=response.json();assert doc['rubrics'][-1]['status']=='DRAFT_AI'
    assert not doc['approvals'] and not doc['correction_available']
    assert client.post(prefix+'/corrections').json()['detail']['code']=='ACCEPTED_TRANSCRIPTION_REQUIRED'


def test_replace_ai_with_teacher_rubric_keeps_lineage_without_ai_authorship(store):
    doc=suggest(store,prepare(store));old=doc['rubrics'][-1]
    doc=store.save_rubric(doc['problem']['problem_id'],SaveRubric(expected_revision=doc['revision'],statement_version=1,
        max_score=10,criteria=CRITERIA,replace_with_teacher=True),ACTOR,base_id=old['rubric_id'])
    assert doc['rubrics'][-1]['provenance']['origin']=='TEACHER'
    assert doc['rubrics'][-1]['generation'] is None
    assert doc['rubrics'][-1]['supersedes_id']==old['rubric_id']
    assert doc['rubrics'][0]==old


def test_committed_dy1_approval_hashes_remain_valid_without_migration():
    from confia_lean_auditor.dynamic.models import DynamicDocument
    raw=json.loads((Path(__file__).parents[1]/'docs/audits/assets/confia-dynamic-dy1/browser-validation.json').read_text())['document']
    # Evidence contains the stored document, not a new fixture generated by DY2.
    from confia_lean_auditor.dynamic.models import RubricVersion, DynamicProblemPackage
    raw={k:v for k,v in raw.items() if k in DynamicDocument.model_fields}
    raw['rubrics']=[{k:v for k,v in r.items() if k in RubricVersion.model_fields} for r in raw['rubrics']]
    raw['packages']=[{k:v for k,v in p.items() if k in DynamicProblemPackage.model_fields} for p in raw['packages']]
    doc=DynamicDocument.model_validate(raw)
    assert doc.approvals and not doc.preparations
    approval=doc.approvals[0]
    package=next(p for p in doc.packages if p.package_id==approval.package_id)
    rubric=next(r for r in doc.rubrics if r.rubric_id==approval.rubric_id)
    assert model_sha256(package)==approval.package_sha256
    assert model_sha256(rubric)==approval.rubric_sha256


def test_real_adapter_wire_schema_provenance_and_no_secret_in_output(monkeypatch):
    from types import SimpleNamespace
    import openai
    captured={};raw=json.dumps(proposal())
    class Client:
        def __init__(self,**kwargs):captured['client']=kwargs;self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kwargs):
            captured['request']=kwargs
            return SimpleNamespace(status='completed',output_text=raw,model='returned-model',id='response-test')
    monkeypatch.setattr(openai,'OpenAI',Client);monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','1')
    monkeypatch.setenv('OPENAI_API_KEY','secret-not-to-persist')
    result,meta=OpenAIPreparationProvider().generate('prepare',{'statement':'x²-5x+6=0'},PreparationProposal)
    assert meta.returned_model=='returned-model' and meta.output_sha256==canonical_sha256(raw)
    assert meta.code_content_sha256 and 'secret-not-to-persist' not in meta.model_dump_json()
    assert not captured['request']['store'] and 'tools' not in captured['request']
    assert captured['client']['max_retries']==0 and captured['client']['timeout']==90
    from confia_lean_auditor.dynamic.provider import generation_schema
    schema=generation_schema(SuggestedRubric.model_json_schema())
    assert schema['properties']['criteria']['maxItems']==8
    assert schema['properties']['max_score']['type']=='string'
    assert schema['required']==list(schema['properties'])


@pytest.mark.parametrize('status,raw,code',[
    ('incomplete','','PROVIDER_INCOMPLETE_OR_REFUSED'),
    ('completed','not-json','PROVIDER_INVALID_OUTPUT'),
    ('completed','{"invented":true}','PROVIDER_INVALID_OUTPUT'),
])
def test_real_adapter_refusal_and_malformed_output_never_become_preparation(monkeypatch,status,raw,code):
    from types import SimpleNamespace
    import openai
    class Client:
        def __init__(self,**kwargs):self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kwargs):return SimpleNamespace(status=status,output_text=raw,model='fixture',id='fixture')
    monkeypatch.setattr(openai,'OpenAI',Client);monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','1');monkeypatch.setenv('OPENAI_API_KEY','unit-test')
    with pytest.raises(ProviderFailure) as caught:OpenAIPreparationProvider().generate('prepare',{},PreparationProposal)
    assert caught.value.code==code and caught.value.provenance.raw_output==raw


def test_expired_running_preparation_can_retry_without_overwriting_history(store):
    from confia_lean_auditor.dynamic.preparation_models import PreparationRecord
    from confia_lean_auditor.dynamic.store import now
    doc=create(store);pid=doc['problem']['problem_id']
    service=PreparationService(store,ControlledProvider())
    with store._locked():
        original,digest=store._owned(pid,ACTOR);package=original.packages[-1]
        pending=PreparationRecord(preparation_id='dprep_'+'1'*32,preparation_version=1,problem_id=pid,
            source_package_id=package.package_id,statement_version=1,statement_sha256=package.statement_sha256,
            status='PENDING',created_at=now()-timedelta(minutes=4),requested_by=ACTOR.actor_id)
        service._append(original,digest,pending,service._event(original,pending,'preparation_pending',ACTOR))
        original,digest=store._owned(pid,ACTOR);running=pending.model_copy(update={'status':'RUNNING'})
        doc=service._append(original,digest,running,service._event(original,running,'preparation_running',ACTOR))
    doc=prepare(store,doc)
    assert doc['preparation_history'][0]['failure_code']=='INTERRUPTED_OR_EXPIRED'
    assert doc['current_preparation']['preparation_version']==2
    assert doc['current_preparation']['status']=='READY_FOR_REVIEW'


def test_expected_unique_answer_with_multiple_values_requires_review():
    p=proposal();p['expects_unique_result']=True
    result=analyze(PreparationProposal.model_validate(p))
    assert 'EXPECTED_UNIQUE_RESULT' in {w.code for w in result.warnings}
    assert result.trust_state=='HUMAN_REVIEW_REQUIRED'


def test_obviously_duplicated_criteria_not_published(store):
    doc=prepare(store);value=suggestion();value['criteria'][1]['description']=value['criteria'][0]['description']
    with pytest.raises(ProviderFailure):suggest(store,doc,ControlledProvider(rubric=value))
    assert not store.get(doc['problem']['problem_id'],ACTOR)['rubrics']


def test_current_endpoint_keeps_exact_approved_preparation_when_new_one_exists(api,monkeypatch):
    clients,_=api;client=clients('teacher.a');doc=api_create(client);prefix='/dynamic/problems/'+doc['problem']['problem_id']
    monkeypatch.setattr(OpenAIPreparationProvider,'generate',ControlledProvider().generate)
    monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','1');monkeypatch.setenv('OPENAI_API_KEY','unit-test')
    doc=client.post(prefix+'/preparations',json={'expected_revision':doc['revision']}).json()
    first=doc['current_preparation']['preparation_id']
    doc=client.post(prefix+'/rubric-suggestion',json={'expected_revision':doc['revision'],'preparation_id':first}).json()
    doc=client.post(prefix+'/rubrics/'+doc['rubrics'][-1]['rubric_id']+'/approve',json={'expected_revision':doc['revision']}).json()
    approved=doc['current_configuration']
    doc=client.post(prefix+'/preparations',json={'expected_revision':doc['revision']}).json()
    current=client.get(prefix+'/current').json()
    assert current['current_configuration']==approved
    assert current['preparation']['preparation_id']==first
    assert current['latest_preparation']['preparation_id']!=first
    assert not current['correction_available']
