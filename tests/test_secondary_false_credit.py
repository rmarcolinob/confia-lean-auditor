"""Regression replay of V4 model proposals, with no external calls."""
import copy,json
from pathlib import Path
import pytest
from confia_lean_auditor.rubric import secondary_adjudicator as s
from tests.test_secondary_adjudicator_contract import fake_client

FIXTURES=Path(__file__).parent/'fixtures/secondary_false_credit_04'
def fixture(cid):return json.loads((FIXTURES/f'{cid}.json').read_text())
BAD=['ITA2025Q1_S014_L04','ITA2025Q3_S002_L01','ITA2025F2Q1_S002_L04']
POS=['ITA2025F2Q1_S003_L02','ITA2025F2Q5_S003_L04','ITA2025F2Q6_S006_L04']
DENY=['ITA2025Q4_S002_L04','ITA2025F2Q5_S024_L04']
@pytest.mark.parametrize('cid',BAD)
def test_v4_false_award_cannot_pass_local_adapter(cid):
 f=fixture(cid);p=f['payload'];d=s.resolve_selections(s.validate_selections(f['proposal'],p),p)
 s.validate_decisions(d,p)
 assert d[f['criterion_id']]['decision']=='deny'
 assert d[f['criterion_id']]['suggested_points']==0

@pytest.mark.parametrize('cid',POS+DENY)
def test_v4_legitimate_controls_preserved(cid):
 f=fixture(cid);p=f['payload'];d=s.resolve_selections(f['proposal'],p);s.validate_decisions(d,p)
 assert d[f['criterion_id']]['decision']==('award' if cid in POS else 'deny')
 assert d[f['criterion_id']]['suggested_points']==f['proposal'][f['criterion_id']]['suggested_points']

@pytest.mark.parametrize('cid',BAD+POS+DENY)
def test_provider_proposal_is_gated_without_retry_or_invalid_response(monkeypatch,cid):
 f=fixture(cid);before=copy.deepcopy(f['proposal']);seen,_=fake_client(monkeypatch,[before])
 d,m=s.adjudicate(f['payload']);row=d[f['criterion_id']]
 assert len(seen)==1 and m['retry_count']==0 and m['validation_status']=='accepted'
 assert row['decision']==('award' if cid in POS else 'deny')
 if cid in BAD:
  gate=m['criteria'][0]['award_gate']
  assert gate['eligible'] is False and gate['model_proposal']['decision']=='award'
  assert gate['reasons'] and row['reason_code']=='INCOMPLETE_FOR_CRITERION'
 assert f['proposal']==before


def synthetic(text, *, description='Conclui corretamente n=7.', selected=None, requirements=None, microclaims=None):
 from confia_lean_auditor.rubric.secondary_candidates import with_candidates
 p={'solution_text':text,'pending_criteria':[{'id':'arbitrary_criterion','description':description,
    'max_points':3,'allowed_points':[0,3],'input_status':'indeterminate','coded_requirements':requirements or [],
    'required_microclaims':microclaims or []}]}
 p=with_candidates(p,s.redact)
 if selected:
  a=text.index(selected);p['pending_criteria'][0]['candidate_evidence']=[{'evidence_id':'E17_4','source_text':selected,
    'source_start':a,'source_end':a+len(selected),'source_kind':'local_context','grounding_status':'grounded'}]
 c=p['pending_criteria'][0]
 d={c['id']:{'decision':'award','suggested_points':3,'evidence_ids':[c['candidate_evidence'][0]['evidence_id']],
     'reason_code':'SATISFIES_CRITERION','rationale':s.selection_rationales(c,'SATISFIES_CRITERION')[0]}}
 return p,d

def applied(p,d):
 out=s.resolve_selections(s.validate_selections(d,p),p);s.validate_decisions(out,p)
 return out['arbitrary_criterion']

@pytest.mark.parametrize('text',[
 'Suponha que:\nn=7', 'Não é verdade que n=7.', 'Tentei n=7. Essa tentativa foi abandonada.',
 'Não n=7.', 'O enunciado diz: "n=7".', 'Assumindo n=7, obtemos um exemplo.',
])
def test_expected_value_in_nonasserted_scope_cannot_award(text):
 p,d=synthetic(text,selected='n=7');assert applied(p,d)['decision']=='deny'


def test_final_answer_only_remains_eligible_without_microclaims():
 p,d=synthetic('Logo n=7.');assert applied(p,d)['decision']=='award'


def test_expected_value_alone_cannot_replace_declared_derivation():
 p,d=synthetic('Logo n=7.',description='Deriva y=2*x+1 a partir da relação declarada.',
  requirements=[{'description':'derived relation','relation_alternatives':[['y=2*x+1']]}],
  microclaims=[{'status':'verified_by_lean','satisfied':True}])
 assert applied(p,d)['decision']=='deny'

@pytest.mark.parametrize('status',['unavailable','no_textual_evidence','formal_steps_not_verified','dependency_not_verified','not_generated'])
def test_missing_required_microclaim_blocks_even_correct_target(status):
 p,d=synthetic('Logo n=7.',microclaims=[{'status':status}]);assert applied(p,d)['decision']=='deny'


def test_dependency_policy_result_cannot_be_overridden_by_verified_label():
 p,d=synthetic('Logo n=7.',microclaims=[{'status':'verified_by_lean','satisfied':False}]);assert applied(p,d)['decision']=='deny'


def test_equivalent_method_in_existing_canonical_domain_is_allowed():
 p,d=synthetic('y=x+x+1',description='Obtém y=2*x+1 ou expressão equivalente.',
  requirements=[{'description':'relation','relation_alternatives':[['y=2*x+1']]}],
  microclaims=[{'status':'verified_by_formal_steps','satisfied':True}])
 assert applied(p,d)['decision']=='award'


def test_no_global_no_microclaim_means_zero_rule():
 p,d=synthetic('Os lados são positivos e distintos.',description='Identifica lados positivos e distintos.')
 assert applied(p,d)['decision']=='award'


def test_correct_relation_with_wrong_sign_is_not_accepted_and_not_id_specific():
 for sign in ['+','-']:
  p,d=synthetic(f'z²=(a²{sign}4,4a)',description='Representa corretamente as coordenadas.',
      requirements=[{'description':'coordinates','relation_alternatives':[['z^2=(a^2-4,4a)']]}])
  assert applied(p,d)['decision']==('award' if sign=='-' else 'deny')


def test_grounded_conflict_blocks_award_even_when_positive_selected():
 p,d=synthetic('n=7. n=8.',selected='n=7')
 p['pending_criteria'][0]['award_grounded_claims']=[{'text':'n=8','source_span':{'start':5,'end':8},'alignment':[{'status':'conflicting'}]}]
 r=applied(p,d);assert r['decision']=='deny' and r['reason_code']=='CONTRADICTS_CRITERION'


def test_stale_conflict_not_bound_to_current_source_is_not_a_veto():
 p,d=synthetic('n=7.')
 p['pending_criteria'][0]['award_grounded_claims']=[{'text':'n=8','source_span':{'start':0,'end':3},'alignment':[{'status':'conflicting'}]}]
 assert applied(p,d)['decision']=='award'


def test_declared_mathematical_negation_is_not_rejected_as_prose_negation():
 p,d=synthetic('g não é injetora.',description='Conclui que g não é injetora.')
 p['pending_criteria'][0]['allowed_mathematical_negations']=[r'g\s+nao\s+e\s+injetora']
 assert applied(p,d)['decision']=='award'


def test_primary_status_and_coverage_remain_unchanged_on_veto(monkeypatch):
 from tests.test_score_policy import inputs
 from confia_lean_auditor.rubric.scoring_policy import apply_scoring_policy
 data=inputs(['supported','indeterminate','refuted']);data['solution']='Suponha que a=1.'
 from tests.secondary_selection_helpers import selection
 fake_client(monkeypatch,[lambda call:selection(json.loads(call['input']))])
 before=[(i.points,i.mathematical_status) for i in data['rubric'].items]
 r=apply_scoring_policy(**data)
 assert [(i.points,i.mathematical_status) for i in r.items]==before
 assert r.coverage==pytest.approx(2/3) and r.score==2 and r.estimated_points==0
 assert r.items[1].suggested_points==0 and r.items[1].mathematical_status=='indeterminate'
 assert r.items[1].scoring_basis=='secondary_adjudication'

@pytest.mark.parametrize('text,selected',[
 ('Se n=7, então podemos prosseguir.','n=7'),
 ('n não é 7.','n não é 7'),
 ('n=7. Essa hipótese foi descartada.','n=7'),
])
def test_additional_nonassertion_forms(text,selected):
 p,d=synthetic(text,selected=selected);assert applied(p,d)['decision']=='deny'


def test_formal_refutation_bound_to_source_vetoes_award():
 from confia_lean_auditor.rubric.secondary_award_gate import can_secondary_award
 f=fixture('ITA2025F2Q5_S024_L04');p=f['payload'];c=p['pending_criteria'][0]
 c['award_verification_results']=[f['refuted_control_check']]
 result=can_secondary_award(c,c['candidate_evidence'][:1],source=p['solution_text'])
 assert not result['eligible'] and 'KNOWN_MATHEMATICAL_CONTRADICTION' in result['reasons']


def test_technical_failure_is_not_treated_as_formal_contradiction():
 from confia_lean_auditor.rubric.secondary_award_gate import can_secondary_award
 f=fixture('ITA2025F2Q5_S024_L04');p=f['payload'];c=p['pending_criteria'][0]
 check=copy.deepcopy(f['refuted_control_check']);check['status']='technical_error';check['refutation_verified']=False
 c['award_verification_results']=[check]
 result=can_secondary_award(c,c['candidate_evidence'][:1],source=p['solution_text'])
 assert 'KNOWN_MATHEMATICAL_CONTRADICTION' not in result['reasons']


def test_correct_conclusion_after_explicit_abandonment_not_erased():
 p,d=synthetic('Tentei n=8 e abandonei. Logo n=7.',selected='n=7')
 assert applied(p,d)['decision']=='award'


def test_current_context_microclaim_policy_and_no_expected_binding_oracle():
 from types import SimpleNamespace
 from confia_lean_auditor.rubric.secondary_context import prepare_payload
 from confia_lean_auditor.core.problem_assets import validate_problem_assets
 from confia_lean_auditor.core.schemas import RubricItemResult
 assets=validate_problem_assets(Path(__file__).resolve().parents[1]/'problems/ITA2025F2Q1','ITA2025F2Q1')
 item=RubricItemResult(id='final_answer',description='Conclui corretamente a=-1 e b=3.',max_points=2,
      mathematical_status='indeterminate',points=None,detected=False)
 p=prepare_payload(pending=[item],solution='a é menos um e b é três.',assets=assets,microclaims=[],student_checks=[])
 c=p['pending_criteria'][0]
 assert c['required_microclaims']==[] and 'expected_bindings' not in c
 assert c['award_verification_results']==[]


def test_microclaim_dependency_status_is_computed_locally_without_mutation():
 from confia_lean_auditor.rubric.secondary_context import prepare_payload
 from confia_lean_auditor.core.problem_assets import validate_problem_assets
 from confia_lean_auditor.core.schemas import RubricItemResult,MicroclaimResult
 assets=validate_problem_assets(Path(__file__).resolve().parents[1]/'problems/ITA2025F2Q1','ITA2025F2Q1')
 item=RubricItemResult(id='reduced_polynomial_form',description='resto',max_points=3,
      mathematical_status='indeterminate',points=None,detected=False)
 mc=MicroclaimResult(id='mc_reduced_polynomial_form',description='resto',claim_types=[],theorem='',
   textual_evidence=True,formal_steps_verified=True,lean_status='verified_by_lean',
   depends_on_microclaim_ids=['missing_dependency'],required_formal_step_types=[],supports_rubric_items=[])
 before=mc.model_dump()
 p=prepare_payload(pending=[item],solution='p(x)=(a+b)x-a',assets=assets,microclaims=[mc],student_checks=[])
 assert p['pending_criteria'][0]['required_microclaims'][0]['satisfied'] is False
 assert mc.model_dump()==before


def test_answer_only_metadata_and_wire_are_unambiguous(monkeypatch):
 from confia_lean_auditor.rubric.secondary_context import prepare_payload
 from confia_lean_auditor.core.problem_assets import validate_problem_assets
 from confia_lean_auditor.core.schemas import RubricItemResult
 from tests.secondary_selection_helpers import selection
 assets=validate_problem_assets(Path(__file__).resolve().parents[1]/'problems/ITA2025F2Q1','ITA2025F2Q1')
 item=RubricItemResult(id='final_answer',description=assets.rubric.items[-1].description,max_points=2,
      mathematical_status='indeterminate',points=None,detected=False)
 p=prepare_payload(pending=[item],solution='a é menos um e b é três, acho que é isso.',assets=assets,microclaims=[],student_checks=[])
 assert p['pending_criteria'][0]['answer_only'] is True
 seen,_=fake_client(monkeypatch,[lambda call:selection(json.loads(call['input']))])
 d,m=s.adjudicate(p);wire=json.loads(seen[0]['input'])['pending_criteria'][0]
 assert wire['answer_only'] is True and 'conclusion_only' not in wire and 'expected_bindings' not in wire
 assert d['final_answer']['decision']=='award'
 assert 'por extenso' in ' '.join(seen[0]['instructions'].split()) and m['prompt_version']=='secondary-award-safety-v2'


def test_derivation_does_not_become_answer_only():
 from confia_lean_auditor.rubric.secondary_award_gate import answer_only
 assert not answer_only({'description':'Deriva a relação X usando Y.'})
 assert not answer_only({'description':'Calcula e justifica a expressão da área.'})


def test_actual_live_false_deny_replays_and_is_not_locally_upgraded(monkeypatch):
 import httpx,openai
 f=fixture('ITA2025F2Q1_S003_L02');entry=f['actual_live_false_deny'];p=json.loads(entry['request_body']['input'])
 p['solution_text']=f['payload']['solution_text'];real=openai.OpenAI;seen=[]
 def transport(request):
  assert request.url.host=='offline.invalid';seen.append(json.loads(request.content))
  return httpx.Response(entry['status_code'],json=entry['response_body'])
 def factory(**kwargs):return real(api_key='offline-only',base_url='https://offline.invalid/v1',http_client=httpx.Client(transport=httpx.MockTransport(transport)),**kwargs)
 monkeypatch.setenv('OPENAI_API_KEY','offline-only');monkeypatch.setattr(openai,'OpenAI',factory)
 d,m=s.adjudicate(p)
 assert len(seen)==1 and d['final_answer']['decision']=='deny' and m['validation_status']=='accepted'
 assert next(t for t in m['criteria'] if t['criterion_id']=='final_answer')['award_gate']=={'not_requested':True}
