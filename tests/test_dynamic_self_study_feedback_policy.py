"""Permanent I6B adversarial regressions. All providers/data are simulated."""
import json
from types import SimpleNamespace
from pathlib import Path
import pytest
from test_core_auth import auth_case
from test_dynamic_self_study import case, prepared, attempt, post, create, confirm, no_grades
from test_dynamic_credit_dependencies import simulated, opinion
from confia_lean_auditor.dynamic import study_service as study, study_feedback as feedback
from confia_lean_auditor.submissions.integrity import canonical_sha256


def override(case,monkeypatch,operation,modify):
    provider=case['provider'];original=provider.generate
    def generate(op,payload,typ):
        value,meta=original(op,payload,typ)
        if op==operation:
            raw=modify(value.model_dump(mode='json'),payload)
            meta=meta.model_copy(update=dict(raw_output=json.dumps(raw),output_sha256=canonical_sha256(raw)))
            return SimpleNamespace(model_dump=lambda **_:raw),meta
        return value,meta
    monkeypatch.setattr(provider,'generate',generate)


def help_url(d,aid):return '/'+d['study_id']+'/attempts/'+aid+'/help'
def refresh(case,d):
    r=case['student'].get('/dynamic/self-study/'+d['study_id']);assert r.status_code==200,r.text
    no_grades(r.json());return r.json()


def test_regression_r1_internal_titles_descriptions_and_ids_never_become_public(case,monkeypatch):
    def score_title(raw,payload):
        raw['criteria'][0].update(title='Sua nota: 1,5/3 pontos',description='Máximo 3 pontos. Resposta final x=6.')
        return raw
    override(case,monkeypatch,'study_rubric',score_title)
    d,aid=attempt(case,prepared(case));public=refresh(case,d)
    assert public['packages'][0]['objectives'][0]['title']=='Objetivo 1'
    assert public['attempts'][0]['report']['findings'][0]['objective']=='Objetivo 1'
    text=json.dumps(public,ensure_ascii=False)
    assert 'Sua nota' not in text and 'Máximo 3 pontos' not in text
    assert public['attempts'][0]['report']['findings'][0]['criterion_id']!= 'reasoning'
    pack=study.package(case['root']/'study'/d['study_id'],d['packages'][0]['package_id'])
    assert pack['rubric']['criteria'][0]['title']=='Sua nota: 1,5/3 pontos'
    assert pack['rubric']['criteria'][0]['max_points']=='3'


@pytest.mark.parametrize('bad',[
 'Sua nota é 1,5/3.',
 'Solução completa: 2x+6=18; 2x=12; x=6.',
 'Resposta final: x=6.',
 'A conclusão foi certificada em Lean.',
])
def test_regression_r2_free_prose_with_valid_quote_is_rejected_and_never_reappears(case,monkeypatch,bad):
    d,aid=attempt(case,prepared(case),text='Subtraio 6: 2x=12. Falta concluir.')
    def inject(raw,payload):raw['items'][0]['message']=bad;return raw
    override(case,monkeypatch,'study_feedback',inject)
    d=post(case['student'],help_url(d,aid),dict(level=2))
    for view in [d,refresh(case,d)]:
        h=view['attempts'][0]['help'][0];assert h['status']=='SAFE_FALLBACK'
        assert bad not in json.dumps(view,ensure_ascii=False)
        assert 'com segurança' in h['content']['items'][0]['message']
    failures=list((case['root']/'study'/d['study_id']/'attempts'/aid/'help_failures').glob('*.json'))
    assert len(failures)==1 and bad in failures[0].read_text()
    path=case['root']/'study'/d['study_id']/'attempts'/aid/'analysis.json'
    original=path.read_bytes();post(case['student'],help_url(d,aid),dict(level=2))
    assert path.read_bytes()==original and len(list(failures[0].parent.glob('*.json')))==1


@pytest.mark.parametrize('field',['limitations','justification','score'])
def test_unapproved_fields_are_rejected_even_outside_message(case,monkeypatch,field):
    d,aid=attempt(case,prepared(case))
    override(case,monkeypatch,'study_feedback',lambda raw,payload:{**raw,field:'Sua nota é 3/3.'})
    d=post(case['student'],help_url(d,aid),dict(level=2))
    assert d['attempts'][0]['help'][0]['status']=='SAFE_FALLBACK'


@pytest.mark.parametrize('level',[2,3])
def test_low_levels_reject_guided_steps_even_without_grade_words(case,monkeypatch,level):
    d,aid=attempt(case,prepared(case))
    if level==3:d=post(case['student'],help_url(d,aid),dict(level=2))
    def steps(raw,payload):raw['items'][0]['steps']=[dict(rule='CONCLUDE',expression='x=6')];return raw
    override(case,monkeypatch,'study_feedback',steps)
    d=post(case['student'],help_url(d,aid),dict(level=level))
    assert d['attempts'][0]['help'][-1]['status']=='SAFE_FALLBACK'


def test_bound_hint_and_concept_preserve_legitimate_numbers_and_fractions(case):
    d=create(case,'Resolva x/2+3=6 e explique.');d=confirm(case,d)
    d=post(case['student'],'/'+d['study_id']+'/prepare');p=d['packages'][0]
    d=post(case['student'],'/'+d['study_id']+'/confirm-interpretation',dict(package_id=p['package_id'],package_sha256=p['sha256'],confirmed=True))
    d,aid=attempt(case,d,text='Subtraio 3: x/2=3. Multiplico por 2: x=6.')
    for level in (2,3):d=post(case['student'],help_url(d,aid),dict(level=level))
    report=d['attempts'][0]['report'];assert report['findings'][0]['evidence'][0]['text']=='Subtraio 3: x/2=3. Multiplico por 2: x=6.'
    assert all(h['status']=='AVAILABLE' for h in d['attempts'][0]['help'])
    assert 'operação' in d['attempts'][0]['help'][0]['content']['items'][0]['message']
    assert 'x=6' not in d['attempts'][0]['help'][0]['content']['items'][0]['message']
    no_grades(d)


def test_level_four_requires_consent_and_only_math_steps_can_be_rendered(case,monkeypatch):
    d,aid=attempt(case,prepared(case))
    for level in (2,3):d=post(case['student'],help_url(d,aid),dict(level=level))
    post(case['student'],help_url(d,aid),dict(level=4),409)
    def guided(raw,payload):
        raw['items'][0]['steps']=[dict(rule='EQUALITY',expression='2*x=12'),dict(rule='SIMPLIFY',expression='x=12/2'),dict(rule='CONCLUDE',expression='x=6')]
        return raw
    override(case,monkeypatch,'study_feedback',guided)
    d=post(case['student'],help_url(d,aid),dict(level=4,request_complete_solution=True))
    h=d['attempts'][0]['help'][-1];assert h['status']=='AVAILABLE' and 'x=12/2' in h['content']['items'][0]['message']
    assert 'não uma conclusão certificada' in h['content']['items'][0]['message']


@pytest.mark.parametrize('expression',['nota=1.5/3','3 pontos','score=3','<script>alert(1)</script>'])
def test_level_four_cannot_smuggle_grade_or_prose_as_expression(case,monkeypatch,expression):
    d,aid=attempt(case,prepared(case))
    for level in (2,3):d=post(case['student'],help_url(d,aid),dict(level=level))
    def guided(raw,payload):raw['items'][0]['steps']=[dict(rule='CONCLUDE',expression=expression)];return raw
    override(case,monkeypatch,'study_feedback',guided)
    d=post(case['student'],help_url(d,aid),dict(level=4,request_complete_solution=True))
    assert d['attempts'][0]['help'][-1]['status']=='SAFE_FALLBACK'
    assert expression not in json.dumps(refresh(case,d))


@pytest.mark.parametrize('g,r,state,finding',[
 ('MATHEMATICAL_ERROR','MATHEMATICAL_ERROR','PARTIAL','MATHEMATICAL_ERROR'),
 ('INCOMPLETE_DEVELOPMENT','INCOMPLETE_DEVELOPMENT','PARTIAL','INCOMPLETE'),
 ('MATHEMATICAL_ERROR','VALID_ARGUMENT','UNCERTAIN','UNCERTAIN'),
 ('VALID_ARGUMENT','MATHEMATICAL_ERROR','UNCERTAIN','UNCERTAIN'),
])
def test_regression_r3_partial_error_incomplete_and_disagreement_remain_distinct(case,monkeypatch,g,r,state,finding):
    simulated(monkeypatch,dict(reasoning=opinion('partial','initial',finding=g)),dict(reasoning=opinion('partial','initial',finding=r)))
    d,aid=attempt(case,prepared(case),text='Subtraio 6: 2x=12. Depois divido: x=7.')
    f=d['attempts'][0]['report']['findings'][0]
    assert (f['state'],f['mathematical_finding'])==(state,finding)
    if finding=='MATHEMATICAL_ERROR':assert 'erro matemático' in f['guidance'] and 'aproveitável' in f['guidance']
    if finding=='INCOMPLETE':assert 'erro' not in f['guidance']
    if state=='UNCERTAIN':assert 'divergem' in f['guidance'] and d['attempts'][0]['report']['status']=='REVIEW_PENDING'
    raw=study.read(case['root']/'study'/d['study_id']/'attempts'/aid/'analysis.json')
    assert raw['grader']['decisions'][0]['suggested_points']=='1.5'
    assert raw['reconciliation'][0]['reconciled_points']=='1.5'
    assert f['evidence'][0]['text'].endswith('x=7.')


def test_provider_failure_returns_safe_guidance_without_changing_audit(case):
    d,aid=attempt(case,prepared(case));case['provider'].fail=True
    path=case['root']/'study'/d['study_id']/'attempts'/aid/'analysis.json';before=path.read_bytes()
    d=post(case['student'],help_url(d,aid),dict(level=2))
    assert d['attempts'][0]['help'][0]['status']=='SAFE_FALLBACK' and path.read_bytes()==before
    assert d['attempts'][0]['report']['findings'][0]['state']=='SUPPORTED'


def test_historical_prose_is_quarantined_without_rewriting_audits(case):
    d,aid=attempt(case,prepared(case));base=case['root']/'study'/d['study_id']/'attempts'/aid
    raw=study.read(base/'analysis.json')
    study.save(base/'help'/'2.json',dict(level=2,requested_at=study.now(),policy_version='self-study-feedback.v1',analysis_sha256=canonical_sha256(raw),content=dict(items=[dict(criterion_id='reasoning',message='Sua nota é 3/3. Resposta final x=6.',quotes=['x=6'])],limitations=['Nota máxima.'])))
    before={p:p.read_bytes() for p in base.rglob('*.json')}
    d=refresh(case,d);assert d['attempts'][0]['help'][0]['status']=='SAFE_FALLBACK'
    assert 'Sua nota' not in json.dumps(d) and all(p.read_bytes()==value for p,value in before.items())


def test_generated_interpretation_and_warnings_cannot_expose_answer_or_points(case,monkeypatch):
    def rewrite(raw,payload):raw.update(normalized_problem='Resposta final x=6; máximo 3 pontos.',uncertainties=['Sua nota é 0/3.']);return raw
    override(case,monkeypatch,'study_prepare',rewrite)
    d=confirm(case,create(case));d=post(case['student'],'/'+d['study_id']+'/prepare')
    assert d['packages'][0]['status']=='NEEDS_CLARIFICATION'
    assert 'máximo 3 pontos' not in json.dumps(d,ensure_ascii=False) and 'Sua nota' not in json.dumps(d)


def test_internal_metadata_and_other_students_remain_inaccessible(case):
    d,aid=attempt(case,prepared(case));base='/dynamic/self-study/'+d['study_id'];sid=d['attempts'][0]['source']['submission_id']
    assert case['clients']('student.b').get(base).status_code==404
    assert case['clients']('student.b').post(base+'/attempts/'+aid+'/help',json=dict(level=2)).status_code==404
    assert case['student'].get(base+'/sources/'+sid+'/assets/analysis.json').status_code==404
    assert case['student'].get(base+'/sources/'+sid+'/assets/provenance.json').status_code==404
    assert case['clients']('teacher.a').get('/submissions/'+sid).status_code==403


@pytest.mark.parametrize('expression',['2×x=12','x=12÷2','x=3/2','x²-5*x+6=0','sqrt(4)=2'])
def test_guided_expression_syntax_preserves_mathematical_notation(expression):
    feedback.validate_expression(expression)


def test_inconclusive_analysis_never_turns_into_guided_solution(case,monkeypatch):
    simulated(monkeypatch,dict(reasoning='review'))
    d,aid=attempt(case,prepared(case))
    assert d['attempts'][0]['report']['status']=='REVIEW_PENDING'
    for level in (2,3):d=post(case['student'],help_url(d,aid),dict(level=level))
    d=post(case['student'],help_url(d,aid),dict(level=4,request_complete_solution=True))
    assert d['attempts'][0]['help'][-1]['status']=='SAFE_FALLBACK'
    assert d['attempts'][0]['report']['findings'][0]['state']=='UNCERTAIN'
