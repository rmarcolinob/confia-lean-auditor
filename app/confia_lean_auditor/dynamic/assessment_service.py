"""Dynamic preparation orchestration on the shared Assessment aggregate.

Publication pins immutable question history. Published definitions never follow a
problem's current pointer; a successor Assessment requires explicit activation.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
from fastapi import HTTPException
from confia_lean_auditor.assessments.models import Assessment, AssessmentDocument, AssessmentItem
from confia_lean_auditor.assessments.store import assessment_store, definition_hash
from .models import PreparationRequest, SuggestionRequest, ApproveRubric
from .grading_context import evaluator_actor, resolve, resolve_pinned
from .store import dynamic_store, DynamicConflict
from .preparation import PreparationService
from .reconciliation_models import POLICY_VERSION


def owned(identifier, user):
    doc = assessment_store().get(identifier)
    if doc.assessment.teacher_user_id != user.user_id or doc.assessment.scope != 'TME':
        raise HTTPException(403, 'Avaliação fora do escopo do avaliador.')
    if doc.assessment.correction_mode != 'DYNAMIC':
        raise DynamicConflict('A operação exige avaliação Dynamic.')
    evaluator_actor(user)
    return doc


def event(doc, kind, user, **details):
    doc.dynamic_revision += 1
    doc.dynamic_events.append(dict(event_id=f'{doc.assessment.assessment_id}:{doc.dynamic_revision}',
        event_type=kind, assessment_id=doc.assessment.assessment_id,
        timestamp=datetime.now(timezone.utc).isoformat(), actor_id=user.user_id, **details))


def record_event(identifier, kind, user, **details):
    store = assessment_store()
    with store._locked():
        doc = store._read(identifier)
        if doc.assessment.teacher_user_id != user.user_id: raise HTTPException(403)
        event(doc, kind, user, **details)
        store._write(doc)


def create(body, user, *, predecessor=None):
    evaluator_actor(user)
    now = datetime.now(timezone.utc)
    doc = AssessmentDocument(assessment=Assessment(
        assessment_id='asmt_'+uuid4().hex, title=body.title, instructions=body.instructions,
        teacher_user_id=user.user_id, academic_year=now.year, scope='TME', schema_version='2.0',
        opens_at=now, closes_at=now+timedelta(days=365), created_at=now,
        correction_mode='DYNAMIC', dynamic_policy_profile=body.policy_profile,
        dynamic_policy_version=POLICY_VERSION, feedback_policy=body.feedback_policy,
        supersedes_assessment_id=predecessor.assessment.assessment_id if predecessor else None))
    if predecessor:
        doc.items = [i.model_copy(update=dict(assessment_id=doc.assessment.assessment_id,
            assessment_item_id='ait_'+uuid4().hex, dynamic_context=None)) for i in predecessor.items]
    event(doc, 'assessment_dynamic_created', user)
    store=assessment_store()
    with store._locked(): store._write(doc)
    return view(doc, user)


def question_readiness(item, actor, published=False):
    data = dynamic_store().get(item.problem_id, actor)
    statement = data['statements'][-1]
    rubric = data['rubrics'][-1] if data['rubrics'] else None
    prep = data['current_preparation']
    blockers=[]; context=None
    try:
        if published:
            context, statement_model, rubric_model, prep_model = resolve_pinned(item.problem_id, actor, item.dynamic_context)
            statement=statement_model.model_dump(mode='json')
            rubric={**rubric_model.model_dump(mode='json'), 'status':'APPROVED'}
            prep=prep_model.model_dump(mode='json')
        else:
            context, _, _, _=resolve(item.problem_id,actor)
    except (DynamicConflict, FileNotFoundError) as exc:
        blockers.append(str(exc) or 'Configuração indisponível.')
    if not prep or prep['status'] != 'READY_FOR_REVIEW': blockers.append('Preparação ausente, em falha ou com revisão pendente.')
    if not rubric or rubric['status'] != 'APPROVED': blockers.append('Rubrica aprovada pendente.')
    if Decimal(str(item.points)) != Decimal(str(statement['max_score'])): blockers.append('Pontos da questão diferem do enunciado; atualize o item antes de ativar.')
    return dict(assessment_item_id=item.assessment_item_id, problem_id=item.problem_id, order=item.order,
        title=statement.get('title') or f'Questão {item.order}', statement=statement['statement'], max_score=item.points,
        statement_version=statement['version_number'], preparation_status=prep['status'] if prep else 'NOT_PREPARED',
        rubric_status=rubric['status'] if rubric else 'MISSING', rubric_id=rubric['rubric_id'] if rubric else None,
        problem_revision=data['revision'], warnings=(prep.get('analysis') or {}).get('warnings',[]) if prep else [],
        ready=not blockers, blockers=list(dict.fromkeys(blockers)), context=context.model_dump(mode='json') if context else None,
        pinned=published, newer_version_available=bool(published and data['current_configuration'] and data['current_configuration']['package']['package_id'] != context.package_id) if context else False)


def view(doc, user):
    actor=evaluator_actor(user); published=doc.assessment.status!='DRAFT'
    rows=[question_readiness(i, actor, published) for i in doc.items]
    ready=bool(rows) and all(r['ready'] for r in rows)
    state='SUPERSEDED' if doc.assessment.superseded_by else 'CLOSED' if doc.assessment.status=='CLOSED' else 'ACTIVE' if published else 'READY' if ready else 'PREPARING' if any(r['preparation_status']!='NOT_PREPARED' for r in rows) else 'DRAFT'
    events=list(doc.dynamic_events)
    for item in doc.items:
        for e in dynamic_store().get(item.problem_id,actor)['events']:
            if e['event_type']=='rubric_approved':
                events.append(dict(**e,assessment_id=doc.assessment.assessment_id,question_id=item.problem_id))
    return dict(**doc.model_dump(mode='json'), readiness=dict(state=state, ready=ready,
        total_questions=len(rows),ready_questions=sum(r['ready'] for r in rows),questions=rows),events=events)


def get(identifier,user): return view(owned(identifier,user),user)


def add(identifier, body, user):
    doc=owned(identifier,user)
    data=dynamic_store().get(body.problem_id,evaluator_actor(user))
    store=assessment_store()
    with store._locked():
        doc=store._read(identifier)
        if doc.assessment.status!='DRAFT' or doc.dynamic_revision!=body.expected_revision:
            raise DynamicConflict('Avaliação mudou ou já foi ativada.')
        if any(i.problem_id==body.problem_id for i in doc.items): raise DynamicConflict('Questão já adicionada.')
        doc.items.append(AssessmentItem(assessment_id=identifier,assessment_item_id='ait_'+uuid4().hex,
            problem_id=body.problem_id,order=len(doc.items)+1,points=float(data['statements'][-1]['max_score'])))
        event(doc,'question_added',user,problem_id=body.problem_id)
        doc=AssessmentDocument.model_validate(doc.model_dump())
        store._write(doc)
    return view(doc,user)


def prepare_many(identifier, body, user):
    doc=owned(identifier,user)
    if doc.assessment.status!='DRAFT': raise DynamicConflict('Crie uma revisão da avaliação antes de preparar novas versões.')
    requested=body.problem_ids or [i.problem_id for i in doc.items]
    if not set(requested)<= {i.problem_id for i in doc.items}: raise DynamicConflict('Questão fora da avaliação.')
    actor=evaluator_actor(user); results=[]
    for pid in requested:
        try:
            data=dynamic_store().get(pid,actor)
            prep=data['current_preparation']
            if body.force or not prep or prep['status']!='READY_FOR_REVIEW':
                record_event(identifier,'question_preparation_started',user,problem_id=pid)
                data=PreparationService(dynamic_store()).start(pid,PreparationRequest(expected_revision=data['revision']),actor)
                prep=data['current_preparation']
                record_event(identifier,'question_preparation_completed',user,problem_id=pid,status=prep['status'])
            if body.generate_rubrics and prep and prep['status']=='READY_FOR_REVIEW' and not data['correction_available']:
                data=PreparationService(dynamic_store()).suggest(pid,SuggestionRequest(expected_revision=data['revision'],preparation_id=prep['preparation_id']),actor)
            results.append(dict(problem_id=pid,status=prep['status'] if prep else 'FAILED'))
        except Exception as exc:
            # Provider failure is isolated; no rollback of other question packages.
            from .provider import ProviderFailure
            if not isinstance(exc,(ValueError,ProviderFailure)): raise
            record_event(identifier,'question_preparation_completed',user,problem_id=pid,status='FAILED')
            results.append(dict(problem_id=pid,status='FAILED',message='Não foi possível concluir esta questão. Revise e tente novamente.'))
    return dict(**get(identifier,user),bulk_results=results)


def approve_many(identifier, body, user):
    doc=owned(identifier,user)
    if doc.assessment.status!='DRAFT': raise DynamicConflict('Avaliação ativa mantém as versões publicadas.')
    actor=evaluator_actor(user); results=[]
    for choice in body.questions:
        if choice.problem_id not in {i.problem_id for i in doc.items}: raise DynamicConflict('Questão fora da avaliação.')
        # Exact selected rubric/revision: bulk is an explicit human action, never blanket approval.
        try:
            dynamic_store().approve(choice.problem_id,choice.rubric_id,
                ApproveRubric(expected_revision=choice.expected_revision,acknowledge_warnings=choice.acknowledge_warnings),actor)
            results.append(dict(problem_id=choice.problem_id,status='APPROVED'))
        except DynamicConflict as exc: results.append(dict(problem_id=choice.problem_id,status='REVIEW_REQUIRED',message=str(exc)))
    return dict(**get(identifier,user),bulk_results=results)


def activate(identifier, body, user):
    owned(identifier,user); store=assessment_store()
    with store._locked():
        doc=store._read(identifier)
        if doc.assessment.status!='DRAFT' or doc.dynamic_revision!=body.expected_revision: raise DynamicConflict('Avaliação mudou ou já foi ativada.')
        ready=view(doc,user)
        if not ready['readiness']['ready']: raise DynamicConflict('Todas as questões precisam de preparação resolvida e rubrica aprovada.')
        from .grading_models import DynamicGradingContext
        doc.items=[i.model_copy(update={'dynamic_context':DynamicGradingContext.model_validate(r['context'])}) for i,r in zip(doc.items,ready['readiness']['questions'])]
        event(doc,'assessment_ready',user)
        doc.assessment=doc.assessment.model_copy(update=dict(status='PUBLISHED',published_at=datetime.now(timezone.utc),definition_sha256=definition_hash(doc)))
        event(doc,'assessment_activated',user)
        doc=AssessmentDocument.model_validate(doc.model_dump())
        store._write(doc)
        previous=doc.assessment.supersedes_assessment_id
        if previous:
            old=store._read(previous)
            old.assessment=old.assessment.model_copy(update=dict(superseded_by=identifier,status='CLOSED',closed_at=datetime.now(timezone.utc)))
            event(old,'assessment_superseded',user,superseded_by=identifier)
            store._write(old)
    return view(doc,user)


def successor(identifier,user):
    old=owned(identifier,user)
    if old.assessment.status=='DRAFT' or old.assessment.superseded_by: raise DynamicConflict('Selecione uma publicação corrente.')
    return create(SimpleNamespace(title=old.assessment.title+' — nova versão',instructions=old.assessment.instructions,
        policy_profile=old.assessment.dynamic_policy_profile,feedback_policy=old.assessment.feedback_policy),user,predecessor=old)


def pinned_activity(case):
    """No locks acquired: also usable inside shared exam/finalization locks."""
    from confia_lean_auditor.tme.exam_store import exam_store
    submission,document,_=exam_store()._manifest(case.exam_submission_id,SimpleNamespace(user_id=case.created_by_user_id))
    item=next((i for i in document.items if i.assessment_item_id==case.assessment_item_id),None)
    a=document.assessment
    if a.correction_mode!='DYNAMIC' or not item or item.dynamic_context!=case.dynamic_context or item.problem_id!=case.problem_id:
        raise DynamicConflict('Questão diverge da publicação da avaliação.')
    return dict(case_id=case.case_id,assessment_id=a.assessment_id,assessment_definition_sha256=a.definition_sha256,
        policy_profile=a.dynamic_policy_profile,policy_version=a.dynamic_policy_version,configured_at=a.published_at.isoformat())
