"""Institutional orchestration of the shared Dynamic workflow, never a grader.

The session student is checked before an internal teacher-owned case is opened.
Only allowlisted student projections leave this service. Source authorship stays
with the student; internal execution is not a teacher's human decision.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from fastapi import HTTPException
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.assessments.store import assessment_store, definition_hash, AssessmentStore
from confia_lean_auditor.assessments.models import AssessmentDocument
from confia_lean_auditor.assessments.router import _student_document, _teacher_classroom, availability
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.submissions.router import store as submissions
from confia_lean_auditor.tme.exam_store import exam_store, sealed, read_sealed, ExamConflict
from confia_lean_auditor.tme.exam_models import TextExamInput, ExamCapturePackage
from confia_lean_auditor.tme import question_review
from confia_lean_auditor.tme.store import case_store
from .school_contracts import SchoolAttemptBinding
from .school_scope import teacher_for
from .grading_context import evaluator_actor, resolve_pinned


def session(user, role):
    if user is None:raise HTTPException(401,'Autenticação necessária.')
    if user.role!=role or not user.active:raise HTTPException(403,'Acesso não autorizado.')
    return user


def lock(identifier=None):
    root=exam_store().folder(identifier) if identifier else exam_store().root
    return AssessmentStore(root/'school_operations')._locked()


def publish(source_id,body,user):
    session(user,Role.TEACHER)
    from .assessment_service import owned,event
    source=owned(source_id,user)
    if source.assessment.scope!='TME' or source.assessment.status!='PUBLISHED':
        raise ExamConflict('Selecione uma atividade Dynamic preparada e publicada.')
    if source.assessment.definition_sha256!=body.source_definition_sha256:raise ExamConflict('A publicação mudou.')
    school,classroom=_teacher_classroom(user,body.school_id,body.classroom_id)
    if source.assessment.dynamic_policy_profile=='SCHOOL_EXAM' and body.policy.feedback=='GUIDANCE':
        raise ExamConflict('Provas exigem divulgação docente.')
    # Verify every pinned package before publishing the new institutional definition.
    for item in source.items:resolve_pinned(item.problem_id,evaluator_actor(user),item.dynamic_context)
    identifier='asmt_'+sha256(f'{user.user_id}:{source_id}:{body.execution_key}'.encode()).hexdigest()[:32]
    request_hash=canonical_sha256(body.model_dump(mode='json'))
    store=assessment_store()
    with store._locked():
        if store._path(identifier).exists():
            previous=store._read(identifier)
            if previous.dynamic_events[0].get('request_sha256')!=request_hash:raise ExamConflict('Chave de publicação já utilizada.')
            return previous
        now=datetime.now(timezone.utc)
        a=source.assessment.model_copy(update=dict(assessment_id=identifier,scope='INSTITUTIONAL',
            school_policy=body.policy,feedback_policy="WITHHOLD" if body.policy.feedback=="WITHHOLD" else "AFTER_CONFIRMATION",network_id=school.network_id,school_id=school.school_id,
            classroom_id=classroom.classroom_id,academic_year=classroom.academic_year,
            opens_at=body.opens_at,closes_at=body.closes_at,created_at=now,published_at=now,
            supersedes_assessment_id=None,superseded_by=None,closed_at=None))
        items=[i.model_copy(update=dict(assessment_id=identifier,assessment_item_id='ait_'+sha256(f'{identifier}:{i.assessment_item_id}'.encode()).hexdigest()[:32])) for i in source.items]
        doc=AssessmentDocument(assessment=a,items=items)
        event(doc,'institutional_activity_published',user,source_assessment_id=source_id,request_sha256=request_hash)
        doc.assessment=doc.assessment.model_copy(update={'definition_sha256':definition_hash(doc)})
        doc=AssessmentDocument.model_validate(doc.model_dump())
        store._write(doc)
    return doc


def activity(identifier,user):
    session(user,Role.STUDENT)
    doc=_student_document(user,identifier)
    if doc.assessment.correction_mode!='DYNAMIC' or not doc.assessment.school_policy:raise HTTPException(404)
    teacher=teacher_for(doc)
    questions=[]
    for item in doc.items:
        _,statement,_,_=resolve_pinned(item.problem_id,evaluator_actor(teacher),item.dynamic_context)
        questions.append(dict(item_id=item.assessment_item_id,order=item.order,title=statement.title or f'Questão {item.order}',
            statement=statement.statement,max_points=item.points,statement_version=statement.version_number))
    return doc,teacher,dict(assessment_id=identifier,title=doc.assessment.title,instructions=doc.assessment.instructions,
        availability=availability(doc.assessment),purpose=doc.assessment.dynamic_policy_profile,
        definition_sha256=doc.assessment.definition_sha256,policy=doc.assessment.school_policy.model_dump(mode='json'),questions=[] if availability(doc.assessment)=='AGENDADO' else questions)


def owned_attempt(identifier,user):
    session(user,Role.STUDENT)
    store=exam_store()
    raw=read_sealed(store.folder(identifier)/'exam.json')
    binding=raw['submission'].get('school_attempt')
    if not binding or binding['student_user_id']!=user.user_id:raise HTTPException(404,'Tentativa não encontrada.')
    doc,teacher,_=activity(raw['submission']['assessment_id'],user)
    detail=store.detail(identifier,teacher)
    if detail.submission.assessment_definition_sha256!=doc.assessment.definition_sha256:raise ExamConflict('Vínculo da publicação inválido.')
    return detail,teacher


def attempts(doc,user,teacher):
    rows=[];store=exam_store()
    for path in store.root.glob('exam_*'):
        raw=read_sealed(store.folder(path.name)/'exam.json')['submission']
        binding=raw.get('school_attempt')
        if binding and raw['assessment_id']==doc.assessment.assessment_id and binding['student_user_id']==user.user_id:
            rows.append(store.detail(path.name,teacher))
    return sorted(rows,key=lambda d:d.submission.school_attempt.attempt_number)


def create_attempt(identifier,body,user):
    doc,teacher,_=activity(identifier,user)
    if body.definition_sha256!=doc.assessment.definition_sha256:raise ExamConflict('Reabra a versão publicada da atividade.')
    a=doc.assessment;policy=a.school_policy
    if body.mode not in policy.allowed_inputs:raise ExamConflict('Entrada não autorizada nesta atividade.')
    if body.mode=='TEXT' and len(body.solutions)!=len(doc.items):raise ExamConflict('Envie uma solução por questão.')
    key='school-'+sha256(f'{identifier}:{user.user_id}:{body.execution_key}'.encode()).hexdigest()
    eid='exam_'+sha256(f'{teacher.user_id}:{key}'.encode()).hexdigest()[:32]
    with lock():
        previous=attempts(doc,user,teacher)
        found=next((d for d in previous if d.submission.submission_id==eid),None)
        if not found and (availability(a)!='DISPONÍVEL' or len(previous)>=policy.max_attempts):
            raise ExamConflict('Prazo encerrado ou limite de tentativas atingido.')
        binding=found.submission.school_attempt if found else SchoolAttemptBinding(student_user_id=user.user_id,
            teacher_user_id=teacher.user_id,attempt_number=len(previous)+1,policy_sha256=canonical_sha256(policy.model_dump(mode='json')))
        common=dict(assessment_identifier=identifier,external_participant_code=f'ALUNO-{sha256(user.user_id.encode()).hexdigest()[:12]}',idempotency_key=key)
        if body.mode=='TEXT':
            detail,created=exam_store().receive_text(TextExamInput(**common,solutions=body.solutions),teacher,school_attempt=binding)
        else:
            package=ExamCapturePackage(**common,original_documents=body.original_documents)
            actual='PDF' if package.original_documents[0].media_type=='application/pdf' else 'IMAGES'
            if actual!=body.mode:raise ExamConflict('Tipo de documento divergente.')
            detail,created=exam_store().receive(package,teacher,school_attempt=binding)
        return student_view(detail,teacher),created


def submitted_path(identifier):return exam_store().folder(identifier)/'school_submission.json'


def editable(detail):
    if submitted_path(detail.submission.submission_id).exists():raise ExamConflict('Tentativa já enviada; uma nova tentativa depende da política docente.')
    if availability(detail.assessment.assessment)!='DISPONÍVEL':raise ExamConflict('Prazo de envio encerrado.')


def child(detail,case_id):
    result=next((c for c in detail.question_attempts if c.case_id==case_id),None)
    if not result:raise HTTPException(404,'Questão fora desta tentativa.')
    return result


def mapping(identifier,body,user):
    with lock(identifier):
        detail,teacher=owned_attempt(identifier,user);editable(detail)
        result=exam_store().update_mapping(identifier,body,teacher,mapping_author=user.user_id)
        return result


def recognize(identifier,case_id,user):
    with lock(identifier):
        detail,teacher=owned_attempt(identifier,user);editable(detail);child(detail,case_id)
        from confia_lean_auditor.recognition.schemas import RecognitionRequest
        from confia_lean_auditor.tme import router
        question_review.recognize(case_id,RecognitionRequest(provider="mathpix_image"),teacher,router.configured_registry())
        return student_view(exam_store().detail(identifier,teacher),teacher)


def save_reading(identifier,case_id,body,user):
    with lock(identifier):
        detail,teacher=owned_attempt(identifier,user);editable(detail);case=child(detail,case_id)
        if case.source_mode=='TEXT':raise ExamConflict('A solução textual original é imutável; use nova tentativa quando autorizada.')
        from confia_lean_auditor.tme.review_models import CreateQuestionTranscription
        from confia_lean_auditor.submissions.schemas import CreateTranscriptionRevisionRequest
        w=question_review.workspace(case_id,teacher);h=w['history']
        if h:
            if body.based_on_revision_number!=h.revisions[-1].revision_number:raise ExamConflict('A leitura mudou.')
            question_review.revise(case_id,h.transcription.transcription_id,CreateTranscriptionRevisionRequest(
                based_on_revision_number=body.based_on_revision_number,reviewer_reference=user.user_id,
                segments=body.segments,status='NEEDS_REVIEW'),teacher)
        else:
            if body.based_on_revision_number!=0:raise ExamConflict('A leitura mudou.')
            question_review.create(case_id,CreateQuestionTranscription(expected_mapping_version=detail.mapping.version,
                segments=body.segments),teacher,reading_author=user.user_id)
        return student_view(exam_store().detail(identifier,teacher),teacher)


def confirm_reading(identifier,case_id,body,user):
    with lock(identifier):
        detail,teacher=owned_attempt(identifier,user);editable(detail);case=child(detail,case_id)
        if case.source_mode!='IMAGE_SCAN':raise ExamConflict('Conferência manuscrita indisponível.')
        exams=exam_store()
        with exams._locked():
            case=question_review.freeze_source(exams,detail,case,teacher)
            store=submissions()
            histories=store.list_transcriptions(case.submission_id)
            if not histories:raise ExamConflict('Transcrição ausente.')
            from confia_lean_auditor.submissions.reading_confirmation import confirm
            with store._locked(exclusive=True):
                proof=confirm(store,case,histories[0].transcription.transcription_id,body,user.user_id,actor_role='STUDENT')
        return proof


def submit(identifier,user):
    # Persist exact selected revisions before the existing services execute. A
    # retry reuses audit/review keys; it cannot purchase a new attempt or a score.
    with lock(identifier):
        detail,teacher=owned_attempt(identifier,user);path=submitted_path(identifier)
        if path.exists():record=read_sealed(path)
        else:
            editable(detail);selected=[]
            for case in detail.question_attempts:
                w=question_review.workspace(case.case_id,teacher);h=w['history']
                if not h:raise ExamConflict('Todas as questões precisam de leitura.')
                if case.source_mode=='IMAGE_SCAN' and w['reading_review']['status']!='CONFIRMED':raise ExamConflict('Confira as transcrições e resolva trechos ilegíveis antes de enviar.')
                latest=h.revisions[-1]
                selected.append(dict(case_id=case.case_id,transcription_id=h.transcription.transcription_id,revision_number=latest.revision_number))
            record=dict(schema_version='school-submission.v1',submitted_by=user.user_id,submitted_at=datetime.now(timezone.utc).isoformat(),
                assessment_definition_sha256=detail.submission.assessment_definition_sha256,selected=selected,
                evaluation_service='dynamic-school-audit.v1')
            SubmissionStore._write_atomic_new(path,json.dumps(sealed(record)).encode())
        if record['submitted_by']!=user.user_id:raise ExamConflict('Autoria do envio inválida.')
        from confia_lean_auditor.submissions.schemas import AcceptTranscriptionRequest
        from confia_lean_auditor.submission_audits.schemas import AuditRequest
        from confia_lean_auditor.submission_audits.router import service as audits
        from confia_lean_auditor.tme.correction_engine import CorrectionEngine
        from .review_service import DynamicReviewService
        from .reconciliation_service import ReconciliationService
        for selection in record['selected']:
            case=child(detail,selection['case_id'])
            w=question_review.workspace(case.case_id,teacher)
            if w['current_human_decision'] or w['exam_finalized']:continue
            if w['history'].revisions[-1].revision_number!=selection['revision_number']:
                raise ExamConflict('Leitura alterada pelo professor; retome pelo workspace docente.')
            store=submissions()
            receipt=store.accept_transcription(selection['transcription_id'],AcceptTranscriptionRequest(
                revision_number=selection['revision_number'],reviewer_reference='dynamic-school-audit.v1',
                reviewer_identity_verified=False,acceptance_note='Vinculação técnica; a conferência humana, quando aplicável, é registrada separadamente.'))
            result=CorrectionEngine().audit_question(case.case_id,AuditRequest(transcription_id=selection['transcription_id'],
                revision_number=selection['revision_number'],acceptance_id=receipt.acceptance.acceptance_id,execution_key='school-submission'),teacher)
            if result['status']!='COMPLETED':continue
            case=case_store().read(case.case_id)
            review=DynamicReviewService(audits()).execute(case,result['audit_run_id'],'school-submission')
            ReconciliationService(audits()).execute(case,result['audit_run_id'],review['review'].review_id if hasattr(review['review'],'review_id') else review['review']['review_id'])
        return student_view(exam_store().detail(identifier,teacher),teacher)


def release(identifier,body,user):
    session(user,Role.TEACHER)
    with lock(identifier):
        detail=exam_store().detail(identifier,user)
        if not detail.submission.school_attempt:raise HTTPException(404)
        teacher_for(detail.assessment)
        from confia_lean_auditor.tme.finalization import lifecycle
        final=lifecycle(identifier)['current_final_correction']
        if not final or final['final_correction_id']!=body.final_correction_id:raise ExamConflict('Finalize e selecione a correção corrente antes da divulgação.')
        if body.release_feedback and detail.assessment.assessment.school_policy.feedback=='WITHHOLD':raise ExamConflict('A política publicada retém explicações.')
        folder=exam_store().folder(identifier)/'school_releases'
        if folder.is_symlink():raise ExamConflict('Armazenamento inválido.')
        folder.mkdir(exist_ok=True)
        index=len(list(folder.glob('*.json')))+1
        value=dict(schema_version='school-release.v1',final_correction_id=final['final_correction_id'],
            final_sha256=canonical_sha256(final),released_by=user.user_id,released_at=datetime.now(timezone.utc).isoformat(),
            release_grade=body.release_grade,release_feedback=body.release_feedback,teacher_feedback=body.teacher_feedback)
        SubmissionStore._write_atomic_new(folder/f'{index:06d}.json',json.dumps(sealed(value)).encode())
        return value


def student_view(detail,teacher):
    identifier=detail.submission.submission_id;a=detail.assessment.assessment;binding=detail.submission.school_attempt
    if not binding:raise HTTPException(404)
    rows=[];submitted=submitted_path(identifier).exists()
    for case in detail.question_attempts:
        w=question_review.workspace(case.case_id,teacher);h=w['history'];revision=h.revisions[-1] if h else None
        audit=w['current_audit'];reconciliation=(audit or {}).get('reconciliation')
        state='DRAFT' if not submitted else 'AWAITING_EVALUATION' if not audit else 'TECHNICAL_ERROR' if audit['status']=='FAILED' or audit.get('technical_uncertainty') else 'REVIEW_PENDING' if not reconciliation or reconciliation.get('reconciled_suggested_score') is None else 'AWAITING_TEACHER'
        if submitted and w['current_human_decision']:state='TEACHER_CONFIRMED'
        row=dict(case_id=case.case_id,item_id=case.assessment_item_id,order=case.question_order,status=state,
            revision_number=revision.revision_number if revision else 0,
            segments=[dict(segment_id=s.segment_id,page_index=s.page_index,order=s.order,kind=s.kind,text=s.text,latex=s.latex) for s in revision.segments] if revision else [],
            reading_review=w.get('reading_review'),pages=[dict(page_index=i,page_number=p.page_number,exam_page_id=p.exam_page_id) for i,p in enumerate(w['pages'])])
        if submitted and a.dynamic_policy_profile=='FORMATIVE_LIST' and a.school_policy.feedback=='GUIDANCE' and audit:
            # No model prose, reference solutions, rubric descriptions or hidden
            # scores are released automatically. Guidance is evidence scoped.
            row['guidance']=[dict(criterion_number=i+1,message='Há evidência de passos aproveitáveis. Confira suas contas e explique por que cada passo é válido.' if c.get('suggested_points') and c.get('status')!='technical_error' else 'Este trecho precisa de revisão. Confira as operações e explicite a justificativa; uma pendência não significa erro ou nota zero.') for i,c in enumerate(audit.get('rubric_items',[]))]
        rows.append(row)
    release_record=None
    from confia_lean_auditor.tme.finalization import lifecycle
    final=lifecycle(identifier)['current_final_correction']
    folder=exam_store().folder(identifier)/'school_releases'
    if folder.is_symlink():raise ExamConflict('Armazenamento inválido.')
    files=sorted(folder.glob('*.json')) if folder.exists() else []
    if final and files:
        r=read_sealed(files[-1])
        if r['final_correction_id']==final['final_correction_id'] and r['final_sha256']==canonical_sha256(final):
            release_record=dict(released_at=r['released_at'],released_by=r['released_by'])
            if r['release_grade']:
                release_record.update(final_total=final['final_total'],max_total=final['max_total'],questions=[dict(order=q['question_order'],final_points=q['final_score'],max_points=q['max_score']) for q in final['questions']])
            if r['release_feedback']:release_record['teacher_feedback']=r['teacher_feedback']
    return dict(attempt_id=identifier,assessment_id=a.assessment_id,attempt_number=binding.attempt_number,
        student_user_id=binding.student_user_id,teacher_user_id=binding.teacher_user_id,
        submitted=submitted,created_at=detail.submission.created_at,status='RELEASED' if release_record else 'SUBMITTED' if submitted else 'DRAFT',
        questions=rows,result=release_record,mapping=detail.mapping.model_dump(mode='json'),
        pages=[dict(page_id=p.exam_page_id,page_number=p.page_number,asset_id=p.original_asset_id,
            preview_url=f'/dynamic/student/attempts/{identifier}/assets/{p.preview_asset_id}',
            original_url=f'/dynamic/student/attempts/{identifier}/assets/{p.original_asset_id}') for p in detail.submission.pages])
