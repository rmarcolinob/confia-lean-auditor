"""Real shared engines with explicitly simulated OCR and semantic opinions."""
from datetime import datetime,timezone
from pathlib import Path
import json,base64
import pytest
from test_core_auth import auth_case
from test_dynamic_credit_dependencies import simulated,opinion
from confia_lean_auditor.dynamic import study_service as study
from confia_lean_auditor.dynamic.preparation_models import GenerationProvenance
from confia_lean_auditor.submissions.integrity import canonical_sha256
from test_tme_full_exam import png

class MockStudyProvider:
    def __init__(self):self.calls=[];self.ambiguous=False;self.fail=False;self.invent=False
    def generate(self,op,payload,typ):
        self.calls.append((op,payload))
        if self.fail:raise TimeoutError('controlled failure')
        if op=='study_prepare':
            value=dict(mathematical_domain='Matemática escolar',normalized_problem=payload['statement']['statement'],data=[],assumptions=[],objects=[],target='Justificar o raciocínio',expects_unique_result=False,candidate_reference_solutions=[],alternative_strategies=[],warnings=[],uncertainties=['Falta informar a medida.'] if self.ambiguous else [])
        elif op=='study_rubric':
            value=dict(max_score='3',criteria=[dict(criterion_id='reasoning',title='Desenvolvimento e justificativa',description='Resolver e justificar com argumentos matemáticos válidos. Aceitar métodos alternativos.',max_points='3',order=1,credit_levels=[dict(level_id='initial',points='1.5',description='Apresentar uma etapa inicial válida, mas sem concluir a justificativa.')])],warnings=[])
        else:
            f=next(f for f in payload['findings'] if f['evidence'])
            value=dict(schema_version='self-study-help.v2',items=[dict(criterion_id=f['criterion_id'],topic='EQUALITY',quotes=['invented'] if self.invent else [f['evidence'][0]['text']],steps=[])])
        result=typ.model_validate(value)
        meta=GenerationProvenance(provider='controlled-test',requested_model='simulated',returned_model='simulated',reasoning_effort=None,prompt_version='test-study.v1',schema_version=typ.__name__,input_sha256=canonical_sha256(payload),output_sha256=canonical_sha256(value),response_id=None,created_at=datetime.now(timezone.utc),code_sha=None,max_output_tokens=1000,raw_output=json.dumps(value))
        return result,meta

@pytest.fixture
def case(auth_case,monkeypatch):
    _,users,clients,root=auth_case
    monkeypatch.setenv('CONFIA_SELF_STUDY_DIR',str(root/'study'))
    monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','0')
    provider=MockStudyProvider();monkeypatch.setattr(study,'provider',lambda:provider)
    calls=simulated(monkeypatch,dict(reasoning='met'))
    return dict(users=users,clients=clients,root=root,student=clients('student.a'),provider=provider,calls=calls)

def post(c,path,body=None,status=200):
    r=c.post('/dynamic/self-study'+path,json=body or {});assert r.status_code==status,r.text
    return r.json()

def create(case,statement='Resolva 2x+6=18 e explique suas operações.',source=None):
    return post(case['student'],'',dict(source=source or dict(text=statement),grade_year=9,execution_key='new'),201)

def confirm(case,d,aid=None):
    row=next(a for a in d['attempts'] if a['attempt_id']==aid) if aid else d
    s=row['source'];path='/'+d['study_id']+(f'/attempts/{aid}' if aid else '')
    return post(case['student'],path+'/confirm-reading',dict(revision_number=s['revision_number'],revision_sha256=s['revision_sha256'],confirmed=True))

def prepared(case,statement='Resolva 2x+6=18 e explique suas operações.'):
    d=confirm(case,create(case,statement));d=post(case['student'],'/'+d['study_id']+'/prepare');p=d['packages'][-1]
    assert p['status']=='AWAITING_CONFIRMATION',p
    return post(case['student'],'/'+d['study_id']+'/confirm-interpretation',dict(package_id=p['package_id'],package_sha256=p['sha256'],confirmed=True))

def attempt(case,d,text='Subtraio 6 dos dois membros: 2x=12. Divido por 2: x=6.',key='first',source=None):
    d=post(case['student'],'/'+d['study_id']+'/attempts',dict(source=source or dict(text=text),package_id=d['packages'][-1]['package_id'],execution_key=key),201)
    aid=d['attempts'][-1]['attempt_id'];d=confirm(case,d,aid)
    return post(case['student'],'/'+d['study_id']+'/attempts/'+aid+'/analyze'),aid

def no_grades(value):
    if isinstance(value,dict):
        assert not set(value)&{'score','max_score','points','max_points','suggested_points','final_total','final_score','reconciled_points','percentage','grade','rank'}
        for v in value.values():no_grades(v)
    elif isinstance(value,list):
        for v in value:no_grades(v)

@pytest.mark.parametrize('statement,solution,state,expected',[
 ('Resolva x²-5x+6=0 em R e justifique.','Fatoro (x-2)(x-3)=0. Pelo produto nulo, x=2 ou x=3.','met','SUPPORTED'),
 ('Resolva x+y=7 e 2x-y=2.','Somando as equações encontro 3x=9, portanto x=3. Falta encontrar y.','partial','PARTIAL'),
 ('Três cadernos custam R$18. Quanto custam cinco?','Cada caderno custa 18/3=6. Cinco custam 5+6=11.','not_met','MATHEMATICAL_ERROR'),
 ('Encontre f(x)=ax+b com f(0)=3 e f(2)=7.','Não sei explicar a relação entre os valores.','review','UNCERTAIN'),
 ('Calcule área e perímetro de um retângulo 8 por 5.','Área 8×5=40 cm². Perímetro 8+5+8+5=26 cm.','met','SUPPORTED'),
 ('Resolva x²-5x+6=0 em R e justifique.','Completo o quadrado: (x-5/2)²=1/4, então x=2 ou 3.','met','SUPPORTED')])
def test_novel_problems_share_engines_and_never_publish_grades(case,monkeypatch,statement,solution,state,expected):
    simulated(monkeypatch,dict(reasoning=opinion(state,'initial' if state=='partial' else None)))
    d,aid=attempt(case,prepared(case,statement),solution)
    report=d['attempts'][0]['report'];assert report['findings'][0]['state']==expected,report
    assert report['formal_verification_performed'] is False
    no_grades(d)
    if expected!='UNCERTAIN':assert report['findings'][0]['evidence'][0]['text'] in solution
    raw=study.read(case['root']/'study'/d['study_id']/'attempts'/aid/'analysis.json')
    assert raw['grader']['context']['semantic_policy']=='dynamic-semantic.v1'
    assert raw['reviewer']['semantic_reviews'] and raw['reconciliation']
    assert not list(case['root'].glob('**/final_corrections/*.json'))


def test_feedback_levels_history_ownership_and_provisional_versions(case,monkeypatch):
    simulated(monkeypatch,dict(reasoning='not_met'))
    d,aid=attempt(case,prepared(case));base='/'+d['study_id']+'/attempts/'+aid
    assert d['attempts'][0]['help']==[]
    post(case['student'],base+'/help',dict(level=4,request_complete_solution=True),409)
    for level in [2,3]:
        d=post(case['student'],base+'/help',dict(level=level));no_grades(d)
    post(case['student'],base+'/help',dict(level=4),409)
    d=post(case['student'],base+'/help',dict(level=4,request_complete_solution=True))
    assert [h['level'] for h in d['attempts'][0]['help']]==[2,3,4]
    assert all(not p['reference_candidates'] for op,p in case['provider'].calls if op=='study_feedback' and p['level']<4)
    path=case['root']/'study'/d['study_id']/'attempts'/aid/'analysis.json';before=path.read_bytes()
    simulated(monkeypatch,dict(reasoning='met'))
    d,second=attempt(case,d,'Aplico a mesma operação aos dois membros e confiro o resultado.','second')
    assert len(d['attempts'])==2 and path.read_bytes()==before
    assert d['attempts'][-1]['report']['comparison'][0]['change']=='ERROR_REVISED'
    for login in ['student.b','teacher.a','manager.a']:
        r=case['clients'](login).get('/dynamic/self-study/'+d['study_id']);assert r.status_code in (403,404)
    sid=d['source']['submission_id']
    assert case['clients']('teacher.a').get('/submissions/'+sid).status_code==403
    assert case['student'].post('/submissions/'+sid+'/recognitions',json={}).status_code==403
    post(case['student'],base+'/reading',dict(based_on_revision_number=1,segments=[dict(segment_id='x',page_index=0,order=0,kind='text',text='Changed')]),409)
    assert 'official_grade_applicable' in d['policy'] and not d['policy']['official_grade_applicable']


def test_ambiguous_statement_and_technical_failures_remain_pending(case,monkeypatch):
    d=confirm(case,create(case,'Calcule a área do triângulo.'))
    case['provider'].ambiguous=True
    d=post(case['student'],'/'+d['study_id']+'/prepare');assert d['packages'][-1]['status']=='NEEDS_CLARIFICATION'
    p=d['packages'][-1];post(case['student'],'/'+d['study_id']+'/confirm-interpretation',dict(package_id=p['package_id'],package_sha256=p['sha256'],confirmed=True),409)
    case['provider'].fail=True
    d=post(case['student'],'/'+d['study_id']+'/prepare');assert d['packages'][-1]['status']=='TECHNICAL_ERROR';no_grades(d)
    case['provider'].fail=False;case['provider'].ambiguous=False
    d=post(case['student'],'/'+d['study_id']+'/prepare');p=d['packages'][-1]
    d=post(case['student'],'/'+d['study_id']+'/confirm-interpretation',dict(package_id=p['package_id'],package_sha256=p['sha256'],confirmed=True))
    simulated(monkeypatch,dict(reasoning='error'))
    d,aid=attempt(case,d);assert d['attempts'][0]['report']['status']=='TECHNICAL_ERROR';no_grades(d)


def test_disagreement_missing_quotes_and_stale_reading(case,monkeypatch):
    simulated(monkeypatch,dict(reasoning=opinion('partial','initial')),dict(reasoning='met'))
    d,aid=attempt(case,prepared(case));assert d['attempts'][0]['report']['findings'][0]['state']=='UNCERTAIN'
    case['provider'].invent=True
    post(case['student'],'/'+d['study_id']+'/attempts/'+aid+'/help',dict(level=2))
    assert study.view(d['study_id'],case['users']['student_a'])['attempts'][0]['help'][0]['status']=='SAFE_FALLBACK'
    s=d['source'];base='/'+d['study_id'];old=dict(revision_number=s['revision_number'],revision_sha256=s['revision_sha256'],confirmed=True)
    post(case['student'],base+'/reading',dict(based_on_revision_number=s['revision_number'],segments=[dict(segment_id='t',page_index=0,order=0,kind='text',text='Um novo enunciado com outra condição.')]))
    post(case['student'],base+'/confirm-reading',old,409)
    post(case['student'],base+'/prepare',{},409)


def test_photos_statement_and_solution_reuse_recognition_and_transcriptions(case,monkeypatch):
    import httpx
    from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider
    from confia_lean_auditor.recognition.registry import RecognizerRegistry
    from confia_lean_auditor.tme import router
    monkeypatch.setenv('CONFIA_MATHPIX_APP_ID','test');monkeypatch.setenv('CONFIA_MATHPIX_APP_KEY','test')
    registry=RecognizerRegistry();registry.register('mathpix_image',lambda:MathpixImageProvider(httpx.MockTransport(lambda _:httpx.Response(200,json={'text':'Texto reconhecido simulado; conferir.'}))))
    monkeypatch.setattr(router,'configured_registry',lambda:registry)
    original=png('white');source=dict(original_documents=[dict(media_type='image/png',content_base64=base64.b64encode(original).decode())])
    d=create(case,source=source);base='/'+d['study_id'];d=post(case['student'],base+'/recognize')
    assert d['source']['automatic'] and not d['source']['confirmed']
    post(case['student'],base+'/prepare',{},409)
    d=post(case['student'],base+'/reading',dict(based_on_revision_number=1,segments=[dict(segment_id='page:0',page_index=0,order=0,kind='text',text='Resolva 2x=12 e justifique.')]))
    d=confirm(case,d);d=post(case['student'],base+'/prepare');p=d['packages'][-1]
    d=post(case['student'],base+'/confirm-interpretation',dict(package_id=p['package_id'],package_sha256=p['sha256'],confirmed=True))
    d=post(case['student'],base+'/attempts',dict(source=source,package_id=p['package_id'],execution_key='photo'),201);aid=d['attempts'][0]['attempt_id']
    d=post(case['student'],base+'/attempts/'+aid+'/recognize');d=confirm(case,d,aid)
    d=post(case['student'],base+'/attempts/'+aid+'/analyze');assert d['attempts'][0]['report']['status']=='FEEDBACK_AVAILABLE',d
    url=d['source']['originals'][0]['url'];assert case['student'].get(url).content==original
    assert case['clients']('student.b').get(url).status_code==404
    sid=d['source']['submission_id'];(case['root']/'submissions'/sid/'original_1.bin').write_bytes(b'corrupted synthetic original')
    assert case['student'].get(url).status_code==409


def test_private_sources_remain_private_when_legacy_demo_is_enabled(case,monkeypatch):
    d=create(case);sid=d['source']['submission_id']
    from confia_lean_auditor.submissions.router import store
    tr=store().list_transcriptions(sid)[0].transcription.transcription_id
    monkeypatch.setenv('CONFIA_AUTH_ENABLED','0')
    client=case['clients']()
    assert client.get('/dynamic/self-study').status_code==401
    assert sid not in client.get('/submissions').text
    for path in ['/submissions/'+sid,'/submissions/'+sid+'/snapshot','/submissions/'+sid+'/transcriptions','/transcriptions/'+tr]:
        assert client.get(path).status_code==401,path


def test_pdf_pages_and_unreadable_reading_require_explicit_resolution(case):
    from test_tme_full_exam import pdf
    original=pdf(2)
    d=create(case,source=dict(original_documents=[dict(media_type='application/pdf',content_base64=base64.b64encode(original).decode())]))
    base='/'+d['study_id'];assert len(d['source']['pages'])==2
    assert case['student'].get(d['source']['originals'][0]['url']).content==original
    segments=[dict(segment_id='p0',page_index=0,order=0,kind='text',text='Um retângulo mede 8 cm por 5 cm.'),
              dict(segment_id='p1',page_index=1,order=0,kind='text',text='Calcule [ilegível].')]
    d=post(case['student'],base+'/reading',dict(based_on_revision_number=0,segments=segments));s=d['source']
    post(case['student'],base+'/confirm-reading',dict(revision_number=s['revision_number'],revision_sha256=s['revision_sha256'],confirmed=True),409)
    segments[1]['text']='Calcule a área e explique a diferença entre área e perímetro.'
    d=post(case['student'],base+'/reading',dict(based_on_revision_number=s['revision_number'],segments=segments))
    d=confirm(case,d);d=post(case['student'],base+'/prepare');p=d['packages'][-1]
    assert p['current_statement'] and 'perímetro' in p['statement']
    assert d['source']['confirmed'] and d['source']['revision_number']==2
    no_grades(d)


def test_revised_statement_keeps_previous_analysis_and_package_pinned(case):
    d,aid=attempt(case,prepared(case));base='/'+d['study_id'];old=d['packages'][-1]
    path=case['root']/'study'/d['study_id']/'attempts'/aid/'analysis.json';saved=path.read_bytes()
    d=post(case['student'],base+'/reading',dict(based_on_revision_number=d['source']['revision_number'],segments=[dict(segment_id='new',page_index=0,order=0,kind='text',text='Resolva 3x=12 e justifique.')]))
    d=confirm(case,d)
    assert not d['packages'][-1]['current_statement']
    assert d['packages'][-1]['statement']==old['statement']
    assert d['attempts'][0]['package_id']==old['package_id'] and path.read_bytes()==saved
    post(case['student'],base+'/attempts',dict(source=dict(text='Outra resolução'),package_id=old['package_id'],execution_key='stale'),409)
    d=post(case['student'],base+'/prepare');assert d['packages'][-1]['version']==2
    assert d['packages'][-1]['current_statement'] and path.read_bytes()==saved


def test_more_than_three_photographs_preserve_all_originals(case):
    original=png('white')
    d=create(case,source=dict(original_documents=[dict(media_type='image/png',content_base64=base64.b64encode(original).decode()) for _ in range(4)]))
    assert len(d['source']['pages'])==len(d['source']['originals'])==4
    for item in d['source']['originals']:
        assert case['student'].get(item['url']).content==original
    assert not d['source']['confirmed']
