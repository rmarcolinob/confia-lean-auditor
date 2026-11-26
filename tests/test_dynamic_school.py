"""Institutional 9th-grade activity. All OCR and semantic opinions are simulated."""
import base64
from datetime import datetime,timedelta,timezone
from decimal import Decimal
import pytest
from test_core_auth import auth_case
from test_dynamic_credit_dependencies import criterion,simulated,opinion
from confia_lean_auditor.dynamic import assessment_service as activities
from confia_lean_auditor.dynamic.assessment_router import Create,Add,Revision
from confia_lean_auditor.dynamic.grading_context import evaluator_actor
from confia_lean_auditor.dynamic.models import CreateProblem,SaveRubric,ApproveRubric
from confia_lean_auditor.dynamic.store import dynamic_store
from confia_lean_auditor.assessments.store import assessment_store
from confia_lean_auditor.submission_audits.router import service
from test_dynamic_handwriting import TEXTS
from test_tme_full_exam import png

@pytest.fixture
def school(auth_case,monkeypatch):
    _,users,clients,root=auth_case
    for key,name in [('CONFIA_DYNAMIC_DIR','dynamic'),('CONFIA_TME_CASES_DIR','cases'),('CONFIA_TME_EXAMS_DIR','exams'),('CONFIA_ASSESSMENTS_DIR','assessments'),('CONFIA_ASSESSMENT_PARTICIPANTS_DIR','participants')]:monkeypatch.setenv(key,str(root/name))
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY','dynamic-semantic.v1')
    monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','0')
    actor=evaluator_actor(users['teacher']);store=dynamic_store()
    cs=[[criterion('fraction',2,1)],[criterion('method',1,1),criterion('answer',1,2,dependencies=['method'],credit_levels=[dict(level_id='division',points='.5',description='Dividir ambos os membros por 2, com erro no resultado.')],dependency_rules=[dict(criterion_id='method',kind='MATHEMATICAL',condition='Obter 2x=12.')])],[criterion('perimeter',2,1)]]
    statements=['Calcule três quartos de 24 e explique.','Resolva 2x+6=18 explicando as operações.','Um retângulo tem lados 5 cm e 3 cm. Calcule o perímetro e justifique.']
    doc=activities.create(Create(title='Matemática — 9º ano',instructions='Justifique suas respostas.',policy_profile='SCHOOL_EXAM'),users['teacher'])
    for criteria,statement in zip(cs,statements):
        p=store.create(CreateProblem(statement=statement,max_score='2',correction_mode='DYNAMIC'),actor)
        p=store.save_rubric(p['problem']['problem_id'],SaveRubric(expected_revision=p['revision'],statement_version=1,max_score='2',criteria=criteria),actor)
        p=store.approve(p['problem']['problem_id'],p['rubrics'][-1]['rubric_id'],ApproveRubric(expected_revision=p['revision']),actor)
        doc=activities.add(doc['assessment']['assessment_id'],Add(expected_revision=doc['dynamic_revision'],problem_id=p['problem']['problem_id']),users['teacher'])
    doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),users['teacher'])
    source=doc['assessment']['assessment_id'];before=assessment_store()._path(source).read_bytes()
    now=datetime.now(timezone.utc)
    teacher=clients('teacher.a');student=clients('student.a')
    body=dict(source_definition_sha256=doc['assessment']['definition_sha256'],school_id='school-a',classroom_id='class-a',opens_at=(now-timedelta(minutes=5)).isoformat(),closes_at=(now+timedelta(days=7)).isoformat(),policy=dict(max_attempts=2),execution_key='publication')
    r=teacher.post(f'/dynamic/assessments/{source}/institutional-publications',json=body);assert r.status_code==201,r.text
    a=r.json()['assessment'];assert a['scope']=='INSTITUTIONAL'
    assert assessment_store()._path(source).read_bytes()==before
    calls=simulated(monkeypatch,dict(fraction='met',method='met',answer=opinion('partial','division'),perimeter='not_met'))
    return dict(root=root,users=users,clients=clients,teacher=teacher,student=student,a=a,calls=calls,source=source,publication=body)


def text_attempt(school,key='first'):
    a=school['a'];r=school['student'].post(f"/dynamic/student/activities/{a['assessment_id']}/attempts",json=dict(definition_sha256=a['definition_sha256'],mode='TEXT',solutions=[' '.join(TEXTS[:2]),TEXTS[2],TEXTS[3]],execution_key=key))
    assert r.status_code in (200,201),r.text
    return r.json()


def test_text_publication_authorship_shared_evaluation_and_disclosure(school):
    s=school['student'];t=school['teacher'];a=school['a'];aid=a['assessment_id']
    public=s.get('/assessments');assert public.status_code==200,public.text
    assert 'dynamic_context' not in public.text and 'dynamic_events' not in public.text
    detail=s.get('/dynamic/student/activities/'+aid);assert detail.status_code==200,detail.text
    assert len(detail.json()['questions'])==3 and 'rubric' not in detail.text
    attempt=text_attempt(school);eid=attempt['attempt_id']
    r=s.post('/dynamic/student/attempts/'+eid+'/submit');assert r.status_code==200,r.text
    assert r.json()['result'] is None and 'suggested_points' not in r.text and 'rubric_items' not in r.text
    from confia_lean_auditor.tme import question_review
    from confia_lean_auditor.tme.store import case_store
    for q,expected in zip(attempt['questions'],[2,1.5,0]):
        c=case_store().read(q['case_id']);w=question_review.workspace(c.case_id,school['users']['teacher']);run=service().get(w['current_audit']['audit_run_id'])
        assert run.result.score==expected
        assert run.source.provenance.school_attempt.student_user_id==school['users']['student_a'].user_id
        from confia_lean_auditor.submissions.router import store
        assert store().get_record(c.submission_id).submitted_by_user_id==school['users']['student_a'].user_id
        assert w['current_audit']['reconciliation']['reconciled_suggested_score'] is not None
    # Student cannot read teacher workspaces, grade or mutate via generic capture.
    cid=attempt['questions'][0]['case_id'];c=case_store().read(cid)
    assert s.get(f'/tme/question-attempts/{cid}/workspace').status_code==403
    assert s.post(f'/submissions/{c.submission_id}/recognitions',json={}).status_code==403
    assert school['clients']('student.b').get('/dynamic/student/attempts/'+eid).status_code==404
    assert school['clients']('teacher.b').get('/dynamic/assessments/'+aid).status_code==403
    assert school['clients']().get('/dynamic/student/activities/'+aid).status_code==401
    assert len(s.get('/dynamic/student/activities/'+aid).json()['attempts'])==1


def finish(school,attempt,adjust=False):
    t=school['teacher'];eid=attempt['attempt_id']
    for q in attempt['questions']:
        base='/tme/cases/'+q['case_id'];w=t.get('/tme/question-attempts/'+q['case_id']+'/workspace');assert w.status_code==200,w.text
        a=w.json()['current_audit'];rec=a['reconciliation']
        body=dict(audit_run_id=a['audit_run_id'],transcription_version_id=a['transcription_version_id'],reconciliation_id=rec['reconciliation_id'],execution_key='confirm',decision_type='ACCEPT_SUGGESTION')
        if adjust and q['order']==2:
            body.update(decision_type='ADJUST_SCORE',final_points='1.5',override_reason='Erro aritmético após operação válida.',adjudication=dict(rubric_sha256=rec['context']['rubric_sha256'],criteria=[dict(criterion_id='method',final_points='1',justification='Transformação equivalente correta.'),dict(criterion_id='answer',final_points='.5',justification='Divisão indicada com erro final.',dependency_justification='A equação anterior foi obtida corretamente.')]))
        r=t.post(base+'/decision',json=body);assert r.status_code==201,r.text
    summary=t.get(f'/tme/exam-submissions/{eid}/correction').json();assert summary['ready_to_finalize'],summary
    r=t.post(f'/tme/exam-submissions/{eid}/correction/finalize',json=dict(expected_snapshot_sha256=summary['snapshot_sha256'],execution_key='final'));assert r.status_code==201,r.text
    return r.json()


def test_disagreement_adjudication_release_and_attempt_quota(school,monkeypatch):
    simulated(monkeypatch,dict(fraction='met',method='met',answer=opinion('partial','division'),perimeter='not_met'),dict(fraction='met',method='met',answer='met',perimeter='not_met'))
    s=school['student'];a=text_attempt(school);eid=a['attempt_id'];base='/dynamic/student/attempts/'+eid
    sent=s.post(base+'/submit');assert sent.status_code==200,sent.text
    assert sent.json()['questions'][1]['status']=='REVIEW_PENDING'
    assert sent.json()['result'] is None
    f=finish(school,a,adjust=True);assert Decimal(f['final_total'])==Decimal('3.5')
    assert s.get(base).json()['result'] is None
    release=dict(final_correction_id=f['final_correction_id'],release_grade=True,release_feedback=True,teacher_feedback='Você explicou bem as frações. Na equação, confira 12 dividido por 2. Para o perímetro, considere os quatro lados.')
    assert s.post('/dynamic/school-attempts/'+eid+'/release',json=release).status_code==403
    assert school['teacher'].post('/dynamic/school-attempts/'+eid+'/release',json=release).status_code==200
    result=s.get(base).json()['result'];assert Decimal(result['final_total'])==Decimal('3.5') and result['teacher_feedback']==release['teacher_feedback']
    # Same key is idempotent; new keys use the published attempt budget.
    text_attempt(school);text_attempt(school,'second')
    r=s.post(f"/dynamic/student/activities/{school['a']['assessment_id']}/attempts",json=dict(definition_sha256=school['a']['definition_sha256'],mode='TEXT',solutions=TEXTS[1:],execution_key='third'))
    assert r.status_code==409
    assert len(s.get('/dynamic/student/activities/'+school['a']['assessment_id']).json()['attempts'])==2


@pytest.mark.parametrize('state,expected',[('review','REVIEW_PENDING'),('error','TECHNICAL_ERROR')])
def test_abstention_and_technical_failure_never_become_zero(school,monkeypatch,state,expected):
    simulated(monkeypatch,dict(fraction=state,method='met',answer='met',perimeter='not_met'))
    a=text_attempt(school);r=school['student'].post('/dynamic/student/attempts/'+a['attempt_id']+'/submit');assert r.status_code==200,r.text
    assert r.json()['questions'][0]['status']==expected and r.json()['result'] is None
    from confia_lean_auditor.tme import question_review
    audit=question_review.workspace(a['questions'][0]['case_id'],school['users']['teacher'])['current_audit']
    assert audit['suggested_score'] is None


def photo_attempt(school):
    a=school['a'];s=school['student'];originals=[png(c) for c in ['red','blue','green']]
    r=s.post(f"/dynamic/student/activities/{a['assessment_id']}/attempts",json=dict(definition_sha256=a['definition_sha256'],mode='IMAGES',original_documents=[dict(media_type='image/png',content_base64=base64.b64encode(b).decode()) for b in originals],execution_key='photos'));assert r.status_code==201,r.text
    attempt=r.json();base='/dynamic/student/attempts/'+attempt['attempt_id']
    bindings=[dict(question_attempt_id=attempt['questions'][q]['case_id'],exam_page_id=attempt['pages'][p]['page_id'],order=i+1) for q,indices in enumerate([[0,1],[1],[2]]) for i,p in enumerate(indices)]
    r=s.put(base+'/page-mapping',json=dict(expected_version=1,bindings=bindings));assert r.status_code==200,r.text
    return s.get(base).json(),originals


def test_photos_scoped_readings_student_confirmation_and_original_integrity(school,monkeypatch):
    import httpx
    from confia_lean_auditor.recognition.registry import RecognizerRegistry
    from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider
    from confia_lean_auditor.tme import router
    monkeypatch.setenv('CONFIA_MATHPIX_APP_ID','test');monkeypatch.setenv('CONFIA_MATHPIX_APP_KEY','test')
    responses=iter([TEXTS[0],TEXTS[1]+'\nOutra questão: '+TEXTS[2]])
    registry=RecognizerRegistry();registry.register('mathpix_image',lambda:MathpixImageProvider(httpx.MockTransport(lambda _:httpx.Response(200,json={'text':next(responses)}))))
    monkeypatch.setattr(router,'configured_registry',lambda:registry)
    a,originals=photo_attempt(school);s=school['student'];base='/dynamic/student/attempts/'+a['attempt_id']
    r=s.post(base+'/questions/'+a['questions'][0]['case_id']+'/recognize');assert r.status_code==200,r.text
    assert r.json()['questions'][0]['reading_review']['automatic']
    assert s.post(base+'/submit').status_code==409
    for q,texts in zip(a['questions'],[TEXTS[:2],[TEXTS[2]],[TEXTS[3]]]):
        current=s.get(base).json();q=next(row for row in current['questions'] if row['case_id']==q['case_id']);url=base+'/questions/'+q['case_id']
        body=dict(based_on_revision_number=q['revision_number'],segments=[dict(segment_id=f'page:{i}',page_index=i,order=0,kind='text',text=t) for i,t in enumerate(texts)])
        r=s.post(url+'/reading',json=body);assert r.status_code==200,r.text
        row=next(row for row in r.json()['questions'] if row['case_id']==q['case_id']);proof=row['reading_review']
        r=s.post(url+'/confirm-reading',json=dict(revision_number=row['revision_number'],revision_sha256=proof['revision_sha256'],confirmed=True,question_scope_confirmed=True));assert r.status_code==200,r.text
        assert r.json()['reviewer_role']=='STUDENT' and r.json()['reviewer_reference']==school['users']['student_a'].user_id
    r=s.post(base+'/submit');assert r.status_code==200,r.text
    assert r.json()['result'] is None
    for q in a['questions']:
        w=school['teacher'].get('/tme/question-attempts/'+q['case_id']+'/workspace').json();run=service().get(w['current_audit']['audit_run_id'])
        assert run.source.provenance.reading_confirmation.reviewer_role=='STUDENT'
        if q['order']==1:assert TEXTS[2] not in run.source.solution_text
        if q['order']==2:assert TEXTS[1] not in run.source.solution_text
    assert s.post(url+'/reading',json=body).status_code==409
    for i,raw in enumerate(originals,1):
        assert s.get(base+f'/assets/original_{i:04d}').content==raw
        assert school['clients']('student.b').get(base+f'/assets/original_{i:04d}').status_code==404
    # Corrupted assets are rejected rather than reinterpreted.
    (school['root']/'exams'/a['attempt_id']/'original_0001').write_bytes(b'corrupted synthetic test')
    assert s.get(base+'/assets/original_0001').status_code==409


def test_publication_pins_policy_and_input_limits_cannot_be_bypassed(school,monkeypatch):
    from confia_lean_auditor.dynamic import school_service
    from confia_lean_auditor.dynamic.models import CreateStatement
    a=school['a'];s=school['student'];t=school['teacher'];aid=a['assessment_id']
    path=assessment_store()._path(aid);before=path.read_bytes()
    d=assessment_store().get(aid);pid=d.items[0].problem_id;actor=evaluator_actor(school['users']['teacher']);store=dynamic_store();p=store.get(pid,actor)
    store.statement(pid,CreateStatement(expected_revision=p['revision'],statement='Novo enunciado não publicado.',max_score='2'),actor)
    assert s.get('/dynamic/student/activities/'+aid).json()['questions'][0]['statement']=='Calcule três quartos de 24 e explique.'
    assert path.read_bytes()==before
    bad=dict(definition_sha256='0'*64,mode='TEXT',solutions=TEXTS[1:],execution_key='bad')
    assert s.post(f'/dynamic/student/activities/{aid}/attempts',json=bad).status_code==409
    assert school['clients']('student.b').get('/dynamic/student/activities/'+aid).status_code==404
    assert t.post('/dynamic/assessments/'+aid+'/successor').status_code==409
    attempt=text_attempt(school);assert s.get('/assessments').json()[0]['submitted_item_ids']==[]
    monkeypatch.setattr(school_service,'availability',lambda _: 'ENCERRADO')
    assert s.post('/dynamic/student/attempts/'+attempt['attempt_id']+'/submit').status_code==409
    assert not school['calls']
    assert s.post(f'/assessments/{aid}/items/{d.items[0].assessment_item_id}/submissions',json={}).status_code in (409,422)


def test_summative_guidance_is_rejected_and_formative_feedback_is_bounded(school,monkeypatch):
    from confia_lean_auditor.dynamic.models import CreateProblem
    from confia_lean_auditor.dynamic.school_router import Publication
    from confia_lean_auditor.dynamic import school_service
    t=school['teacher'];body=dict(school['publication'],execution_key='unsafe',policy=dict(feedback='GUIDANCE'))
    assert t.post('/dynamic/assessments/'+school['source']+'/institutional-publications',json=body).status_code==409
    # A separately prepared formative activity reuses the already approved packages.
    user=school['users']['teacher'];d=activities.create(Create(title='Prática do 9º ano',policy_profile='FORMATIVE_LIST'),user)
    for item in assessment_store().get(school['source']).items:d=activities.add(d['assessment']['assessment_id'],Add(expected_revision=d['dynamic_revision'],problem_id=item.problem_id),user)
    d=activities.activate(d['assessment']['assessment_id'],Revision(expected_revision=d['dynamic_revision']),user)
    body.update(source_definition_sha256=d['assessment']['definition_sha256'],execution_key='formative')
    r=t.post('/dynamic/assessments/'+d['assessment']['assessment_id']+'/institutional-publications',json=body);assert r.status_code==201,r.text
    school['a']=r.json()['assessment'];a=text_attempt(school)
    r=school['student'].post('/dynamic/student/attempts/'+a['attempt_id']+'/submit');assert r.status_code==200,r.text
    assert all(q.get('guidance') for q in r.json()['questions']) and r.json()['result'] is None
    assert 'rubric' not in r.text and 'suggested_score' not in r.text and 'candidate_reference_solutions' not in r.text


def test_isolation_same_class_other_school_and_scheduled_statement(school):
    from confia_lean_auditor.auth.store import AuthStore
    from confia_lean_auditor.auth.models import Role
    from confia_lean_auditor.institutional.store import institutional_store
    from confia_lean_auditor.institutional.models import Classroom,Enrollment
    from test_core_auth import PASSWORD
    store=AuthStore(school['root']/'auth');institutions=institutional_store();data=institutions.snapshot();year=school['a']['academic_year']
    peers=store.create_user(login='peer.test',display_name='Colega sintético',role=Role.STUDENT,password=PASSWORD,tenant_id='school-a',classroom_ids=['class-a'])
    outsider=store.create_user(login='outside.test',display_name='Outra escola sintética',role=Role.STUDENT,password=PASSWORD,tenant_id='school-b',classroom_ids=['class-other'])
    data.classrooms.append(Classroom(classroom_id='class-other',school_id='school-b',name='9º B',grade='9º ano',shift='Manhã',academic_year=year))
    data.enrollments.extend([Enrollment(student_user_id=peers.user_id,school_id='school-a',classroom_id='class-a',academic_year=year),Enrollment(student_user_id=outsider.user_id,school_id='school-b',classroom_id='class-other',academic_year=year)])
    institutions.replace(data)
    a=text_attempt(school);peer=school['clients']('peer.test');other=school['clients']('outside.test');aid=school['a']['assessment_id']
    assert peer.get('/dynamic/student/activities/'+aid).json()['attempts']==[]
    assert peer.get('/dynamic/student/attempts/'+a['attempt_id']).status_code==404
    assert other.get('/dynamic/student/activities/'+aid).status_code==404
    now=datetime.now(timezone.utc)
    body=dict(school['publication'],execution_key='scheduled',opens_at=(now+timedelta(days=1)).isoformat(),closes_at=(now+timedelta(days=2)).isoformat())
    r=school['teacher'].post('/dynamic/assessments/'+school['source']+'/institutional-publications',json=body);assert r.status_code==201,r.text
    future=r.json()['assessment'];view=school['student'].get('/dynamic/student/activities/'+future['assessment_id']).json();assert view['questions']==[] and view['availability']=='AGENDADO'
