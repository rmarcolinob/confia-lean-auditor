"""Whole-exam closure over current AuditRuns and HumanDecisions, never math.

Lock order: exam -> submissions (exclusive for closure/reopening). Submission
writers check this ledger while holding their own lock, without reacquiring exam.
Capture manifests, human decisions and closure versions remain immutable.
"""
from datetime import datetime, timezone
from decimal import Decimal
import json
from typing import Literal, Optional
from uuid import uuid4

from fastapi import HTTPException
from pydantic import Field, model_validator
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.submissions.store import SubmissionStore, SubmissionConflict
from confia_lean_auditor.teacher_decisions.models import Points
from .exam_store import exam_store, ExamConflict
from .human_decisions import HumanDecision, project as project_human

ClosureStatus = Literal['IN_PROGRESS', 'READY_TO_FINALIZE', 'FINALIZED', 'REOPENED']


class FinalizeRequest(SubmissionModel):
    expected_snapshot_sha256: Sha256
    execution_key: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')


class ReopenCorrection(SubmissionModel):
    final_correction_id: str = Field(pattern=r'^final_[0-9a-f]{32}$')
    execution_key: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')


class ConfirmedQuestion(SubmissionModel):
    question_attempt_id: str
    question_order: int
    problem_id: str
    transcription_version_id: str
    audit_run_id: str
    human_decision_id: str
    suggested_score: Points
    final_score: Points
    adjustment: Decimal
    max_score: Decimal
    review_required: bool
    engine_mode: str
    engine_version: str
    human_decision: HumanDecision

    @model_validator(mode='after')
    def coherent(self):
        d = self.human_decision
        if (self.question_attempt_id != d.question_attempt_id or self.transcription_version_id != d.transcription_version_id
                or self.audit_run_id != d.audit_run_id or self.human_decision_id != d.human_decision_id
                or self.suggested_score != d.suggested_points or self.final_score != d.final_points
                or self.adjustment != d.adjustment_delta or self.max_score != d.max_points
                or self.review_required != d.review_required_snapshot
                or (self.engine_mode, self.engine_version) != (d.engine_mode, d.engine_version)):
            raise ValueError('inconsistent question snapshot')
        return self


class FinalCorrection(SubmissionModel):
    final_correction_id: str = Field(pattern=r'^final_[0-9a-f]{32}$')
    assessment_id: str
    assessment_title: str
    assessment_definition_sha256: Sha256
    submission_id: str
    participant_id: str
    participant_code: str
    status: Literal['FINALIZED'] = 'FINALIZED'
    suggested_total_snapshot: Decimal
    final_total: Decimal
    total_adjustment: Decimal
    max_total: Decimal
    question_count: int = Field(ge=1)
    confirmed_question_count: int
    review_question_count: int
    adjusted_question_count: int
    finalized_at: datetime
    finalized_by: str
    version: int = Field(ge=1)
    previous_final_correction_id: Optional[str] = None
    snapshot_sha256: Sha256
    questions: list[ConfirmedQuestion] = Field(min_length=1)

    @model_validator(mode='after')
    def coherent(self):
        qs = self.questions
        if (self.question_count != len(qs) or self.confirmed_question_count != len(qs)
                or len({q.question_attempt_id for q in qs}) != len(qs)
                or self.suggested_total_snapshot != sum(q.suggested_score for q in qs)
                or self.final_total != sum(q.final_score for q in qs)
                or self.max_total != sum(q.max_score for q in qs)
                or self.total_adjustment != self.final_total - self.suggested_total_snapshot
                or self.review_question_count != sum(q.review_required for q in qs)
                or self.adjusted_question_count != sum(q.adjustment != 0 for q in qs)
                or any((q.human_decision.assessment_id, q.human_decision.submission_id, q.human_decision.participant_id)
                       != (self.assessment_id, self.submission_id, self.participant_id) for q in qs)):
            raise ValueError('inconsistent exam totals or scope')
        return self


def records(exam_id):
    folder = exam_store().folder(exam_id) / 'finalizations'
    if folder.is_symlink(): raise ExamConflict('invalid closure directory')
    chain, previous = [], None
    for i, path in enumerate(sorted(folder.glob('*.json')), 1):
        try:
            if path.is_symlink() or path.name != f'{i:06d}.json': raise ValueError()
            record = json.loads(path.read_bytes())
            digest = record.pop('sha256')
            if record['sequence'] != i or record['previous_sha256'] != previous or canonical_sha256(record) != digest:
                raise ValueError()
            if record['kind'] not in {'finalize', 'reopen', 'blocked'} or record['submission_id'] != exam_id:
                raise ValueError()
            if record['kind'] == 'finalize':
                final = FinalCorrection.model_validate(record['final_correction'])
                if final.submission_id != exam_id: raise ValueError()
            record['sha256'] = digest
        except (KeyError, TypeError, ValueError):
            raise ExamConflict('invalid closure history') from None
        chain.append(record); previous = digest
    return chain


def lifecycle(exam_id):
    chain = records(exam_id)
    finals = [r['final_correction'] for r in chain if r['kind'] == 'finalize']
    last = next((r for r in reversed(chain) if r['kind'] != 'blocked'), None)
    current = last['final_correction'] if last and last['kind'] == 'finalize' else None
    return dict(current_final_correction=current, final_corrections=list(reversed(finals)),
                reopened=bool(last and last['kind'] == 'reopen'),
                events=[e for r in chain for e in r['events']])


def assert_editable(exam_id):
    """Caller holds exam or submissions lock; no nested locks here."""
    if lifecycle(exam_id)['current_final_correction']:
        raise SubmissionConflict('Reabra explicitamente a correção antes de alterar a prova finalizada.')


def submission_editable(record):
    if record.tme_case_id:
        from .store import case_store
        case = case_store().read(record.tme_case_id)
        if case.exam_submission_id: assert_editable(case.exam_submission_id)


def _summary(detail, submissions, audits):
    """Caller holds exam and submissions locks; only unlocked store readers."""
    from confia_lean_auditor.submission_audits.schemas import AuditRunView
    from .correction_engine import project_audit
    from .question_review import snapshot_for
    from .review_models import QuestionSourceSnapshot
    eid = detail.submission.submission_id
    life = lifecycle(eid)
    if audits.root.is_symlink(): raise ExamConflict('invalid audit directory')
    all_runs = sorted((audits._read(p.stem) for p in audits.root.glob('aud_*.json')),
                      key=lambda r:r.created_at, reverse=True)
    rows, blockers = [], []
    for case in detail.question_attempts:
        histories = []
        if case.submission_id:
            submissions.assert_submission_integrity(case.submission_id)
            source = QuestionSourceSnapshot.model_validate_json((submissions._folder(case.submission_id)/'snapshot.json').read_bytes())
            if source.model_dump(exclude={'mapping_version'}) != snapshot_for(detail, case).model_dump(exclude={'mapping_version'}):
                raise ExamConflict('frozen source does not match question')
            folder = submissions._transcriptions_folder(case.submission_id)
            if folder:
                histories = sorted((submissions._history_from_folder(p) for p in folder.iterdir()
                    if p.is_dir() and not p.is_symlink() and submissions._transcription_name_valid(p.name)),
                    key=lambda h:h.transcription.created_at, reverse=True)
        version = f'{histories[0].transcription.transcription_id}:{histories[0].revisions[-1].revision_number}' if histories else None
        versions = [dict(version_id=f'{v.transcription_id}:{v.revision_number}', created_at=v.created_at,
                         current=f'{v.transcription_id}:{v.revision_number}' == version)
                    for h in histories for v in h.revisions]
        runs = [AuditRunView(**r.model_dump(), stale=f'{r.transcription_id}:{r.revision_number}' != version)
                for r in all_runs if r.submission_id == case.submission_id]
        run = next((r for r in runs if not r.stale), None)
        audit = project_audit(run, case, detail) if run else None
        human = project_human(case, runs, versions)['current_human_decision']
        reason = None
        if not version: reason = 'Leitura pendente.'
        elif not run: reason = 'Análise anterior desatualizada; reanálise necessária.' if runs else 'Análise pendente.'
        elif run.status == 'FAILED': reason = 'A análise corrente falhou; reanálise necessária.'
        elif audit['suggested_score'] is None: reason = 'Análise sem pontuação disponível.'
        elif not human: reason = 'Questão ainda não confirmada; homologue a análise corrente.'
        suggested = Decimal(str(audit['suggested_score'])) if audit and run.status == 'COMPLETED' and audit['suggested_score'] is not None else None
        d = HumanDecision.model_validate({k:v for k,v in human.items() if k in HumanDecision.model_fields}) if human else None
        if d and (d.final_points < 0 or d.final_points > case.max_score or d.max_points != case.max_score or d.suggested_points != suggested):
            reason = 'Pontuação da decisão não corresponde à análise ou aos limites da questão.'
        row = dict(question_attempt_id=case.case_id, question_order=case.question_order, problem_id=case.problem_id,
            transcription_version_id=version, audit_run_id=run.audit_run_id if run else None,
            human_decision_id=d.human_decision_id if d else None,
            suggested_score=str(suggested) if suggested is not None else None,
            final_score=str(d.final_points) if d else None, adjustment=str(d.adjustment_delta) if d else None,
            max_score=str(case.max_score), review_required=bool(audit and audit['review_required']),
            engine_mode=audit['engine_mode'] if audit else None, engine_version=audit['engine_version'] if audit else None,
            human_decision=d.model_dump(mode='json') if d else None,
            status='CONFIRMED' if d and not reason else 'PENDING' if not version else 'REVIEW', blocker=reason)
        rows.append(row)
        if reason: blockers.append(dict(question_attempt_id=case.case_id, question_order=case.question_order, reason=reason))
    # _detail checks the exact assessment item set/order and limits before here.
    scored = [Decimal(r['suggested_score']) for r in rows if r['suggested_score'] is not None]
    confirmed = [r for r in rows if r['status'] == 'CONFIRMED']
    suggested = sum(scored, Decimal(0)) if scored else None
    final = sum((Decimal(r['final_score']) for r in confirmed), Decimal(0)) if confirmed else None
    complete = len(scored) == len(rows)
    state = 'FINALIZED' if life['current_final_correction'] else 'REOPENED' if life['reopened'] else 'READY_TO_FINALIZE' if not blockers else 'IN_PROGRESS'
    result = dict(assessment_id=detail.submission.assessment_id, assessment_title=detail.assessment.assessment.title,
        assessment_definition_sha256=detail.submission.assessment_definition_sha256,
        submission_id=eid, participant_id=detail.submission.participant_id, participant_code=detail.participant.external_code,
        status=state, ready_to_finalize=not blockers and not life['current_final_correction'],
        question_count=len(rows), confirmed_question_count=len(confirmed), pending_question_count=len(rows)-len(confirmed),
        review_question_count=sum(r['review_required'] for r in rows),
        unconfirmed_review_question_count=sum(r['status']=='REVIEW' for r in rows),
        adjusted_question_count=sum(Decimal(r['adjustment']) != 0 for r in confirmed),
        suggested_total=str(suggested) if suggested is not None else None, suggested_total_complete=complete,
        final_total=str(final) if final is not None else None, final_total_complete=len(confirmed)==len(rows),
        total_adjustment=str(final-suggested) if complete and len(confirmed)==len(rows) else None,
        max_total=str(sum((c.max_score for c in detail.question_attempts), Decimal(0))),
        questions=rows, blockers=blockers, **life)
    binding = dict(assessment_definition_sha256=result['assessment_definition_sha256'], submission_id=eid,
        mapping_version=detail.mapping.version, questions=rows, status=state,
        latest_final_correction_id=life['final_corrections'][0]['final_correction_id'] if life['final_corrections'] else None)
    result['snapshot_sha256'] = canonical_sha256(binding)
    return result


def summary(exam_id, user):
    from confia_lean_auditor.submissions.router import store
    from confia_lean_auditor.submission_audits.router import service
    with exam_store()._locked():
        detail = exam_store()._detail(exam_id, user)
        with store()._locked(exclusive=True):
            return _summary(detail, store(), service())


def _event(kind, data, now, key, **extra):
    return dict(event_id=f'{data["submission_id"]}:{key}:{kind}', event_type=kind, timestamp=now.isoformat(),
        assessment_id=data['assessment_id'], participant_id=data['participant_id'], submission_id=data['submission_id'], **extra)


def _append(exam_id, chain, kind, body, user, events, final=None):
    folder = exam_store().folder(exam_id)/'finalizations'
    folder.mkdir(exist_ok=True, mode=0o700)
    record = dict(sequence=len(chain)+1, previous_sha256=chain[-1]['sha256'] if chain else None,
        submission_id=exam_id, kind=kind, request_sha256=canonical_sha256(body.model_dump(mode='json')),
        execution_key=body.execution_key, actor_id=user.user_id, events=events, final_correction=final)
    record['sha256'] = canonical_sha256(record)
    SubmissionStore._write_atomic_new(folder/f'{record["sequence"]:06d}.json', json.dumps(record, ensure_ascii=False, indent=2).encode())


def finalize(exam_id, body, user):
    from confia_lean_auditor.submissions.router import store
    from confia_lean_auditor.submission_audits.router import service
    with exam_store()._locked():
        detail = exam_store()._detail(exam_id, user)
        with store()._locked(exclusive=True):
            chain = records(exam_id)
            replay = next((r for r in chain if r['execution_key'] == body.execution_key), None)
            if replay:
                if replay['request_sha256'] != canonical_sha256(body.model_dump(mode='json')) or replay['kind'] == 'reopen':
                    raise ExamConflict('execution key already used')
                if replay['kind'] == 'blocked': raise HTTPException(409, replay['events'][-1]['reason'])
                return FinalCorrection.model_validate(replay['final_correction'])
            data = _summary(detail, store(), service())
            now = datetime.now(timezone.utc)
            events = [_event('finalization_requested', data, now, body.execution_key, expected_snapshot_sha256=body.expected_snapshot_sha256)]
            reason = ('A prova mudou desde o resumo. Confira a versão atual.' if data['snapshot_sha256'] != body.expected_snapshot_sha256
                      else 'Reabra explicitamente a correção finalizada.' if data['current_final_correction']
                      else 'Existem questões pendentes de análise ou confirmação.' if data['blockers'] else None)
            if reason:
                events.append(_event('finalization_blocked', data, now, body.execution_key, reason=reason, blockers=data['blockers']))
                _append(exam_id, chain, 'blocked', body, user, events)
                raise HTTPException(409, dict(message=reason, blockers=data['blockers']))
            previous = data['final_corrections'][0] if data['final_corrections'] else None
            final = FinalCorrection(final_correction_id='final_'+uuid4().hex,
                **{k:data[k] for k in ('assessment_id','assessment_title','assessment_definition_sha256','submission_id','participant_id','participant_code',
                    'final_total','total_adjustment','max_total','question_count','confirmed_question_count','review_question_count','adjusted_question_count')},
                suggested_total_snapshot=data['suggested_total'], finalized_at=now, finalized_by=user.user_id,
                version=(previous['version']+1) if previous else 1, previous_final_correction_id=previous['final_correction_id'] if previous else None,
                snapshot_sha256=data['snapshot_sha256'], questions=[{k:v for k,v in r.items() if k in ConfirmedQuestion.model_fields} for r in data['questions']])
            snapshot = final.model_dump(mode='json')
            events.append(_event('correction_finalized', data, now, body.execution_key,
                **{k:snapshot[k] for k in ('final_correction_id','question_count','final_total','total_adjustment','adjusted_question_count','review_question_count')},
                suggested_total=snapshot['suggested_total_snapshot'], human_decision_ids=[q.human_decision_id for q in final.questions],
                engines=[dict(engine_mode=m,engine_version=v) for m,v in sorted({(q.engine_mode,q.engine_version) for q in final.questions})]))
            if previous: events.append(_event('final_correction_superseded', data, now, body.execution_key,
                final_correction_id=previous['final_correction_id'], superseded_by=final.final_correction_id))
            _append(exam_id, chain, 'finalize', body, user, events, snapshot)
            return final


def reopen(exam_id, body, user):
    from confia_lean_auditor.submissions.router import store
    with exam_store()._locked():
        detail = exam_store()._detail(exam_id, user)
        with store()._locked(exclusive=True):
            chain = records(exam_id)
            replay = next((r for r in chain if r['execution_key']==body.execution_key), None)
            if replay:
                if replay['kind'] != 'reopen' or replay['request_sha256'] != canonical_sha256(body.model_dump(mode='json')):
                    raise ExamConflict('execution key already used')
                return dict(reopened_final_correction_id=body.final_correction_id)
            current = lifecycle(exam_id)['current_final_correction']
            if not current or current['final_correction_id'] != body.final_correction_id:
                raise ExamConflict('closure no longer current')
            event = _event('correction_reopened', current, datetime.now(timezone.utc), body.execution_key,
                final_correction_id=body.final_correction_id, actor_id=user.user_id)
            _append(exam_id, chain, 'reopen', body, user, [event])
            return dict(reopened_final_correction_id=body.final_correction_id)


def gold_rows(final):
    return [dict(participant_code=final['participant_code'], assessment_id=final['assessment_id'],
        submission_id=final['submission_id'], final_correction_id=final['final_correction_id'], version=final['version'],
        **{k:q[k] for k in ('question_attempt_id','question_order','problem_id','suggested_score','final_score','adjustment',
            'audit_run_id','transcription_version_id','human_decision_id','review_required','engine_mode','engine_version')}) for q in final['questions']]
