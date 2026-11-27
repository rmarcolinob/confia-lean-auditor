"""DY6 shared Assessment and pinned publication contracts."""
from types import SimpleNamespace
from copy import deepcopy
import pytest
from test_dynamic_dy3 import setup, prepared, ACTOR, CRITERIA
from confia_lean_auditor.dynamic import assessment_service as activities
from confia_lean_auditor.dynamic.assessment_router import Create, Add, Revision
from confia_lean_auditor.dynamic.store import DynamicConflict, dynamic_store
from confia_lean_auditor.dynamic.models import CreateStatement
from confia_lean_auditor.tme.auth import TMEEvaluator, DEMO_EVALUATOR_ID
from confia_lean_auditor.assessments.store import assessment_store

USER=TMEEvaluator(DEMO_EVALUATOR_ID)
@pytest.fixture(autouse=True)
def isolate_assessments(tmp_path,monkeypatch):
    monkeypatch.setenv('CONFIA_ASSESSMENTS_DIR',str(tmp_path/'assessments'))


def activity(profile='FORMATIVE_LIST'):
    return activities.create(Create(title='Lista de álgebra',policy_profile=profile),USER)


def add_question(doc, problem=None):
    problem=problem or prepared()
    return activities.add(doc['assessment']['assessment_id'],Add(expected_revision=doc['dynamic_revision'],problem_id=problem['problem']['problem_id']),USER)


@pytest.mark.parametrize('profile',['FORMATIVE_LIST','SCHOOL_EXAM'])
def test_multiquestion_readiness_explicit_profile_and_activation(setup,profile):
    doc=activity(profile)
    assert doc['readiness']['state']=='DRAFT'
    for _ in range(3): doc=add_question(doc)
    assert doc['readiness']['ready_questions']==3 and doc['readiness']['state']=='READY'
    published=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
    assert published['readiness']['state']=='ACTIVE'
    saved=assessment_store().get(doc['assessment']['assessment_id'])
    assert saved.assessment.correction_mode=='DYNAMIC' and saved.assessment.dynamic_policy_profile==profile
    assert all(i.dynamic_context and i.dynamic_context.rubric_id for i in saved.items)
    assert [i.order for i in saved.items]==[1,2,3]
    assert {'assessment_dynamic_created','question_added','assessment_ready','assessment_activated'}<={e['event_type'] for e in published['events']}


def test_missing_rubric_blocks_activation(setup):
    from confia_lean_auditor.dynamic.models import CreateProblem
    problem=dynamic_store().create(CreateProblem(title='Sem rubrica',statement='Resolva x+1=2.',max_score='10',correction_mode='DYNAMIC'),ACTOR)
    doc=add_question(activity(),problem)
    assert not doc['readiness']['ready'] and doc['readiness']['questions'][0]['rubric_status']=='MISSING'
    with pytest.raises(DynamicConflict):activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)


def test_active_pins_survive_new_statement_and_successor_requires_approval(setup):
    problem=prepared(); doc=add_question(activity(),problem);aid=doc['assessment']['assessment_id']
    doc=activities.activate(aid,Revision(expected_revision=doc['dynamic_revision']),USER)
    before=assessment_store()._path(aid).read_bytes()
    dynamic_store().statement(problem['problem']['problem_id'],CreateStatement(expected_revision=problem['revision'],statement='Resolva x-7=0.',max_score='10'),ACTOR)
    current=activities.get(aid,USER)
    assert current['readiness']['state']=='ACTIVE' and current['readiness']['questions'][0]['statement_version']==1
    assert assessment_store()._path(aid).read_bytes()==before
    successor=activities.successor(aid,USER)
    assert successor['assessment']['supersedes_assessment_id']==aid and not successor['readiness']['ready']
    assert activities.get(aid,USER)['readiness']['state']=='ACTIVE'


def test_ownership_and_revision_conflicts(setup):
    doc=activity();aid=doc['assessment']['assessment_id']
    from fastapi import HTTPException
    with pytest.raises(HTTPException):activities.owned(aid,SimpleNamespace(user_id='another'))
    with pytest.raises(DynamicConflict):activities.add(aid,Add(expected_revision=0,problem_id=prepared()['problem']['problem_id']),USER)


def test_bulk_failure_isolated_and_explicit_rubric_approval(setup,monkeypatch):
    from test_dynamic_dy2 import ControlledProvider
    from confia_lean_auditor.dynamic.provider import ProviderFailure
    from confia_lean_auditor.dynamic.preparation import PreparationService
    from confia_lean_auditor.dynamic.models import CreateProblem
    from confia_lean_auditor.dynamic.assessment_router import Prepare, Approve, Approval
    class SelectiveProvider(ControlledProvider):
        def generate(self,operation,payload,response_type):
            if operation=='prepare' and payload['statement']['title']=='Falha':raise ProviderFailure('CONTROLLED_FAILURE')
            return super().generate(operation,payload,response_type)
    provider=SelectiveProvider()
    monkeypatch.setattr(activities,'PreparationService',lambda store:PreparationService(store,provider))
    doc=activity()
    for title in ['Boa','Falha']:
        problem=dynamic_store().create(CreateProblem(title=title,statement='Resolva x²-5x+6=0.',max_score='10',correction_mode='DYNAMIC'),ACTOR)
        doc=add_question(doc,problem)
    aid=doc['assessment']['assessment_id']
    result=activities.prepare_many(aid,Prepare(),USER)
    assert [r['status'] for r in result['bulk_results']]==['READY_FOR_REVIEW','FAILED']
    good=result['readiness']['questions'][0]
    assert good['rubric_status']=='DRAFT_AI' and not result['readiness']['ready']
    result=activities.approve_many(aid,Approve(questions=[Approval(problem_id=good['problem_id'],rubric_id=good['rubric_id'],expected_revision=good['problem_revision'])]),USER)
    assert result['readiness']['questions'][0]['ready'] and not result['readiness']['ready']
    # Retry only the failed question; successful preparation/rubric bytes stay intact.
    before=dynamic_store().get(good['problem_id'],ACTOR)
    provider.failure=None
    monkeypatch.setattr(activities,'PreparationService',lambda store:PreparationService(store,ControlledProvider()))
    result=activities.prepare_many(aid,Prepare(problem_ids=[result['readiness']['questions'][1]['problem_id']]),USER)
    assert dynamic_store().get(good['problem_id'],ACTOR)==before
    second=result['readiness']['questions'][1]
    result=activities.approve_many(aid,Approve(questions=[Approval(problem_id=second['problem_id'],rubric_id=second['rubric_id'],expected_revision=second['problem_revision'])]),USER)
    assert result['readiness']['state']=='READY'


def test_api_preparation_requires_explicit_profile_and_owner(setup):
    _,client=setup
    assert client.post('/dynamic/assessments',json={'title':'Sem perfil'}).status_code==422
    response=client.post('/dynamic/assessments',json={'title':'Prova publicada','policy_profile':'SCHOOL_EXAM'})
    assert response.status_code==201,response.text
    doc=response.json()
    response=client.post(f"/dynamic/assessments/{doc['assessment']['assessment_id']}/activate",json={'expected_revision':doc['dynamic_revision']})
    assert response.status_code==409


def receive(client, doc, solutions, participant='S1'):
    response=client.post('/tme/exam-submissions/text',json=dict(assessment_identifier=doc['assessment']['assessment_id'],external_participant_code=participant,idempotency_key=participant,solutions=solutions))
    assert response.status_code in (200,201),response.text
    return response.json()


def audit_question(client, case):
    base=f"/tme/cases/{case['case_id']}"
    history=client.get(base+'/transcriptions').json()[0]
    tid=history['transcription']['transcription_id']; rev=history['latest_revision']['revision_number']
    accepted=client.post(base+f'/transcriptions/{tid}/accept',json=dict(revision_number=rev,reviewer_identity_verified=False))
    assert accepted.status_code==200,accepted.text
    response=client.post(base+'/audits',json=dict(transcription_id=tid,revision_number=rev,acceptance_id=accepted.json()['acceptance']['acceptance_id'],execution_key=f'grade{rev}'))
    assert response.status_code==200,response.text
    return response.json()


def test_shared_text_exam_vertical(setup,monkeypatch):
    from test_dynamic_dy3 import FACTOR
    from test_dynamic_dy4 import ReviewerProvider
    from confia_lean_auditor.dynamic.review_service import DynamicReviewService
    from confia_lean_auditor.submission_audits.router import service
    import confia_lean_auditor.dynamic.router as router
    _,client=setup
    doc=add_question(activity());doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
    exam=receive(client,doc,[FACTOR]);case=exam['question_attempts'][0]
    assert receive(client,doc,[FACTOR])['submission']['submission_id']==exam['submission']['submission_id']
    run=audit_question(client,case)
    assert run['status']=='COMPLETED' and run['suggested_score']==10,run
    assert not run['suggestion_ready']
    monkeypatch.setattr(router,'independent_review_service',lambda:DynamicReviewService(service(),ReviewerProvider()))
    url=f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}"
    response=client.post(url+'/independent-reviews',json={'execution_key':'r1'})
    assert response.status_code==201,response.text
    review=response.json()['review']
    response=client.post(url+'/reconciliations',json={'independent_review_id':review['review_id']})
    assert response.status_code==201,response.text
    rec=response.json()['reconciliation']
    response=client.post(f"/tme/cases/{case['case_id']}/decision",json=dict(audit_run_id=run['audit_run_id'],transcription_version_id=run['transcription_version_id'],reconciliation_id=rec['reconciliation_id'],decision_type='ACCEPT_SUGGESTION',execution_key='confirm1'))
    assert response.status_code==201,response.text
    assert response.json()['reconciliation_id']==rec['reconciliation_id']
    from test_tme_finalization import summary,finalize
    eid=exam['submission']['submission_id']
    assert summary(client,eid)['ready_to_finalize']
    assert finalize(client,eid)['final_total']=='10.0'


def reconciled_question(client,case,run,monkeypatch,provider=None):
    from test_dynamic_dy4 import ReviewerProvider
    from confia_lean_auditor.dynamic.review_service import DynamicReviewService
    from confia_lean_auditor.submission_audits.router import service
    import confia_lean_auditor.dynamic.router as router
    monkeypatch.setattr(router,'independent_review_service',lambda:DynamicReviewService(service(),provider or ReviewerProvider()))
    url=f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}"
    response=client.post(url+'/independent-reviews',json={'execution_key':'r1'})
    assert response.status_code==201,response.text
    response=client.post(url+'/reconciliations',json={'independent_review_id':response.json()['review']['review_id']})
    assert response.status_code==201,response.text
    return response.json()['reconciliation']


def confirm_question(client,case,run,rec):
    body=dict(audit_run_id=run['audit_run_id'],transcription_version_id=run['transcription_version_id'],reconciliation_id=rec['reconciliation_id'],decision_type='ACCEPT_SUGGESTION',execution_key='confirm1')
    response=client.post(f"/tme/cases/{case['case_id']}/decision",json=body)
    assert response.status_code==201,response.text
    return response.json(),body


@pytest.mark.parametrize('profile,count',[('FORMATIVE_LIST',3),('SCHOOL_EXAM',2)])
def test_multi_participants_shared_progress_finalize_and_closure(setup,monkeypatch,profile,count):
    from test_dynamic_dy3 import FACTOR
    from test_dynamic_dy4 import ReviewerProvider
    from test_tme_finalization import summary,finalize
    root,client=setup
    doc=activity(profile)
    questions=[prepared(),prepared('Resolva nos reais: 3z+6=0.'),prepared('Resolva nos reais: x/3=4/2.')]
    solutions=[FACTOR,'3z=-6; z=-2; S={-2}; 3*(-2)+6=0','x/3-2=0; x=6; S={6}; 6/3=4/2']
    for p in questions[:count]:doc=add_question(doc,p)
    doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
    participants=[]
    for index,texts in enumerate([solutions[:count],['y=9','z=-2','x=8'][:count]]):
        exam=receive(client,doc,texts,f'ALUNO{index}');eid=exam['submission']['submission_id'];participants.append(exam['submission']['participant_id'])
        assert not summary(client,eid)['ready_to_finalize']
        for case in exam['question_attempts']:
            run=audit_question(client,case)
            if index==0: assert run['suggested_score']==10,run
            # Deliberately conservative reviewer forces a divergence without consulting grader.
            provider=ReviewerProvider(points=('0','0','0'),refs=[[],[],[]],statuses=('INSUFFICIENT',)*3)
            rec=reconciled_question(client,case,run,monkeypatch,provider)
            if profile=='SCHOOL_EXAM':assert float(rec['reconciled_suggested_score'])==run['suggested_score']
            raw=(root/'audits'/f"{run['audit_run_id']}.json").read_bytes()
            confirm_question(client,case,run,rec)
            assert (root/'audits'/f"{run['audit_run_id']}.json").read_bytes()==raw
        assert summary(client,eid)['confirmed_question_count']==count
        final=finalize(client,eid)
        assert len(final['questions'])==count
        last=exam['question_attempts'][-1]
        url=f"/dynamic/attempts/{last['case_id']}/audits/{run['audit_run_id']}/independent-reviews"
        assert client.post(url,json={'execution_key':'afterclose'}).status_code==409
    assert len(set(participants))==2
    listing=client.get('/tme/exam-submissions').json()
    assert len(listing)==2 and all(e['status']=='FINALIZED' for e in listing)
    from confia_lean_auditor.tme.home_summary import rebuild_index
    rebuild_index()
    assert client.get('/tme/cases?view=queue').status_code==200


def test_capture_origin_equivalence_revision_invalidation_and_quality_gate(setup,monkeypatch):
    from datetime import datetime,timezone
    from uuid import uuid4
    from test_dynamic_dy3 import FACTOR
    from confia_lean_auditor.submissions.store import SubmissionStore
    from confia_lean_auditor.submissions.schemas import TranscriptionRecord,TranscriptionRevision,CaptureImportProvenance
    root,client=setup
    doc=add_question(activity());doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
    manual=receive(client,doc,[FACTOR],'typed')['question_attempts'][0]
    typed=audit_question(client,manual)
    original_create=SubmissionStore.create_transcription
    def fake_capture(store,sid,request):
        # Minimal upstream fixture: no OCR, images, segmentation or altered math code.
        from confia_lean_auditor.tme.store import case_store
        source=store.get_record(sid);case=case_store().read(source.tme_case_id)
        record=TranscriptionRecord(transcription_id='tr_'+uuid4().hex,submission_id=sid,created_at=datetime.now(timezone.utc),source='capture',capture_origin=CaptureImportProvenance(exam_submission_id=case.exam_submission_id,producer='machine_transcribed',producer_version='fixture-v1',page_ids=[]))
        version=TranscriptionRevision(**record.model_dump(),revision_number=1,reviewer_reference=USER.user_id,change_type='initial_transcription',segments=request.segments,status='NEEDS_REVIEW')
        with store._locked(exclusive=True):return store._publish_transcription(record,version)
    monkeypatch.setattr(SubmissionStore,'create_transcription',fake_capture)
    machine=receive(client,doc,[FACTOR],'machine')['question_attempts'][0]
    monkeypatch.setattr(SubmissionStore,'create_transcription',original_create)
    run=audit_question(client,machine)
    assert typed['suggested_score']==run['suggested_score']==10
    assert [(i['rubric_item_id'],i['suggested_points'],i['status']) for i in typed['rubric_items']]==[(i['rubric_item_id'],i['suggested_points'],i['status']) for i in run['rubric_items']]
    rec=reconciled_question(client,machine,run,monkeypatch);confirm_question(client,machine,run,rec)
    raw=(root/'audits'/f"{run['audit_run_id']}.json").read_bytes()
    base=f"/tme/cases/{machine['case_id']}";tid=run['transcription_id']
    change=dict(based_on_revision_number=1,change_reason='Professor corrigiu a leitura',segments=[dict(segment_id='text:0',page_index=0,order=0,kind='text',text='y=9')])
    response=client.post(base+f'/transcriptions/{tid}/revisions',json=change)
    assert response.status_code==201,response.text
    assert client.post(base+f'/transcriptions/{tid}/revisions',json=change).status_code==409
    workspace=client.get(f"/tme/question-attempts/{machine['case_id']}/workspace").json()
    assert workspace['current_human_decision'] is None and workspace['audits'][0]['stale']
    assert len(workspace['versions'])==2 and workspace['current_version']['origin']=='human'
    assert (root/'audits'/f"{run['audit_run_id']}.json").read_bytes()==raw
    assert audit_question(client,machine)['suggested_score']==0
    change.update(based_on_revision_number=2,input_issues=[dict(code='AMBIGUOUS_SYMBOL',message='Sinal ilegível')])
    assert client.post(base+f'/transcriptions/{tid}/revisions',json=change).status_code==201
    accepted=client.post(base+f'/transcriptions/{tid}/accept',json={'revision_number':3}).json()
    response=client.post(base+'/audits',json=dict(transcription_id=tid,revision_number=3,acceptance_id=accepted['acceptance']['acceptance_id'],execution_key='invalid'))
    assert response.status_code==409,response.text
    assert 'entrada' in response.text
    assert len(list((root/'audits').glob('aud_*.json')))==3
    assert client.post('/tme/exam-submissions/text',json=dict(assessment_identifier=doc['assessment']['assessment_id'],external_participant_code='bad',idempotency_key='bad',solutions=['   '])).status_code==422


def test_published_rubric_update_and_new_review_preserve_history(setup,monkeypatch):
    from test_dynamic_dy3 import FACTOR
    from confia_lean_auditor.dynamic.models import SaveRubric
    root,client=setup
    p=prepared();doc=add_question(activity(),p);doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
    case=receive(client,doc,[FACTOR])['question_attempts'][0];run=audit_question(client,case)
    rec=reconciled_question(client,case,run,monkeypatch);decision,_=confirm_question(client,case,run,rec)
    old=(root/'audits'/f"{run['audit_run_id']}.json").read_bytes()
    dynamic_store().save_rubric(p['problem']['problem_id'],SaveRubric(expected_revision=p['revision'],statement_version=1,max_score='10',criteria=CRITERIA),ACTOR,base_id=p['rubrics'][-1]['rubric_id'])
    url=f"/tme/question-attempts/{case['case_id']}/workspace"
    workspace=client.get(url).json()
    assert not workspace['audits'][0]['stale'] and workspace['current_human_decision']['human_decision_id']==decision['human_decision_id']
    assert workspace['student_feedback']['status']=='WITHHELD'
    from confia_lean_auditor.dynamic.feedback import question_feedback
    assert question_feedback(workspace['current_audit'],workspace['current_human_decision'],'AFTER_CONFIRMATION')['status']=='AVAILABLE_AFTER_CONFIRMATION'
    response=client.post(f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}/independent-reviews",json={'execution_key':'newreview'})
    assert response.status_code==201,response.text
    invalidated=client.get(url).json()
    assert invalidated['current_human_decision'] is None
    event=next(e for e in invalidated['events'] if e['event_type']=='confirmation_invalidated_by_reconciliation_change')
    assert event['timestamp']>decision['decided_at']
    assert (root/'audits'/f"{run['audit_run_id']}.json").read_bytes()==old


def test_input_port_requires_valid_association_and_nonempty_text(setup):
    from confia_lean_auditor.dynamic.solution_input import require_usable,InputRequiresReview
    source=SimpleNamespace(problem_id='dyn_valid',submission_id='sub_valid',solution_text='x=1',provenance=SimpleNamespace(revision=SimpleNamespace(input_issues=[],segments=[])),warnings=[])
    with pytest.raises(InputRequiresReview):require_usable(source,SimpleNamespace(problem_id='dyn_wrong',submission_id='sub_valid'))
    source.solution_text='  '
    with pytest.raises(InputRequiresReview):require_usable(source,SimpleNamespace(problem_id='dyn_valid',submission_id='sub_valid'))


def test_confirmation_hash_binds_internal_artifact_not_public_redaction(setup,monkeypatch):
    from test_dynamic_dy3 import FACTOR
    from confia_lean_auditor.dynamic import reconciliation_service as module
    from confia_lean_auditor.submissions.integrity import canonical_sha256
    original=module.reconcile_criteria
    def with_private_diagnostic(*args):
        rows=original(*args)
        return [rows[0].model_copy(update={'reason':'Detalhe interno /private/test/provider.log'}),*rows[1:]]
    monkeypatch.setattr(module,'reconcile_criteria',with_private_diagnostic)
    _,client=setup
    doc=add_question(activity());doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
    case=receive(client,doc,[FACTOR])['question_attempts'][0];run=audit_question(client,case)
    rec=reconciled_question(client,case,run,monkeypatch)
    decision,_=confirm_question(client,case,run,rec)
    workspace=client.get(f"/tme/question-attempts/{case['case_id']}/workspace").json()
    assert workspace['current_human_decision']['human_decision_id']==decision['human_decision_id']
    assert workspace['current_audit']['reconciliation']['criteria'][0]['reason']=='[local path hidden]'
    from confia_lean_auditor.dynamic.product_adapter import current_reconciliation
    from confia_lean_auditor.tme.store import case_store
    from confia_lean_auditor.submission_audits.router import service
    persisted=current_reconciliation(case_store().read(case['case_id']),service().get(run['audit_run_id']))
    assert decision['reconciliation_sha256']==canonical_sha256(persisted)
