"""Append-only human decisions over the product audit contract, independent of math.

Mutation lock order: question operation -> exam -> submissions. Audits take the
same question operation lock; reading edits only take exam, so D4 remains valid.
Current confirmation and invalidation events are derived, never written by GET.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
import fcntl
import os
from uuid import uuid4
from typing import Literal, Optional

from pydantic import Field, model_validator
from confia_lean_auditor.submissions.schemas import SubmissionModel
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.teacher_decisions.models import Points
from .models import EvaluatorDecision
from .store import case_store
from .exam_store import exam_store, ExamConflict


class HumanDecisionRequest(SubmissionModel):
    audit_run_id: str = Field(pattern=r"^aud_[0-9a-f]{64}$")
    transcription_version_id: str = Field(pattern=r"^tr_[0-9a-f]{32}:[1-9][0-9]*$")
    decision_type: Literal['ACCEPT_SUGGESTION', 'ADJUST_SCORE']
    final_points: Optional[Points] = None
    override_reason: Optional[str] = Field(default=None, max_length=2000)
    expected_last_decision_id: Optional[str] = Field(default=None, pattern=r"^hdec_[0-9a-f]{32}$")
    execution_key: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


class ReopenQuestion(SubmissionModel):
    human_decision_id: str = Field(pattern=r"^hdec_[0-9a-f]{32}$")
    execution_key: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


class HumanRubricDecision(SubmissionModel):
    rubric_item_id: str
    suggested_points: Optional[Points] = None
    final_points: Points
    adjustment_reason: Optional[str] = Field(default=None, max_length=2000)


class HumanDecision(EvaluatorDecision):
    human_decision_id: str = Field(pattern=r"^hdec_[0-9a-f]{32}$")
    question_attempt_id: str
    assessment_id: str
    participant_id: str
    submission_id: str
    transcription_version_id: str
    engine_mode: str
    engine_version: str
    review_required_snapshot: bool
    review_reasons_snapshot: list[str]
    adjustment_delta: Decimal = Field(decimal_places=2)
    decision_type: Literal['ACCEPT_SUGGESTION', 'ADJUST_SCORE']
    supersedes_decision_id: Optional[str] = None
    status: Literal['CONFIRMED'] = 'CONFIRMED'
    rubric_decisions: list[HumanRubricDecision] = Field(default_factory=list)

    @model_validator(mode='after')
    def coherent_human(self):
        if self.suggested_points is None or not self.audit_run_id or self.case_id != self.question_attempt_id:
            raise ValueError('decision requires an audit suggestion and question')
        if self.final_points > self.max_points or self.adjustment_delta != self.final_points - self.suggested_points:
            raise ValueError('invalid final score or delta')
        if self.decision_type == 'ACCEPT_SUGGESTION' and self.adjustment_delta != 0:
            raise ValueError('accept must preserve suggestion')
        if self.adjustment_delta and not (self.override_reason or '').strip():
            raise ValueError('adjustment reason required')
        return self


@contextmanager
def question_lock(case_id, user):
    store = case_store()
    store.for_user(case_id, user)
    fd = os.open(store.folder(case_id) / '.human-operation.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a+b') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def records(case):
    folder = case_store().folder(case.case_id) / 'human_decisions'
    if folder.is_symlink(): raise ExamConflict('invalid decision directory')
    if not folder.exists(): return []
    import json
    chain, previous = [], None
    for index, path in enumerate(sorted(folder.glob('*.json')), 1):
        if path.is_symlink() or path.name != f'{index:06d}.json': raise ExamConflict('invalid decision chain')
        try:
            record = json.loads(path.read_bytes())
            digest = record.pop('sha256')
            if record['sequence'] != index or record['previous_sha256'] != previous or canonical_sha256(record) != digest:
                raise ValueError('digest mismatch')
            decision = HumanDecision.model_validate(record['decision'])
            if decision.question_attempt_id != case.case_id or decision.submission_id != case.exam_submission_id:
                raise ValueError('decision scope mismatch')
            if record['kind'] not in {'confirm', 'reopen'}: raise ValueError('unknown decision operation')
        except (KeyError, ValueError, TypeError): raise ExamConflict('invalid human decision history') from None
        record['sha256'] = digest
        chain.append(record); previous = digest
    return chain


def append(case, chain, kind, decision, request, user):
    folder = case_store().folder(case.case_id) / 'human_decisions'
    folder.mkdir(exist_ok=True, mode=0o700)
    record = dict(sequence=len(chain)+1, previous_sha256=chain[-1]['sha256'] if chain else None,
        kind=kind, decision=decision.model_dump(mode='json'), timestamp=datetime.now(timezone.utc).isoformat(),
        actor_id=user.user_id, execution_key=request.execution_key, request_sha256=canonical_sha256(request.model_dump(mode='json')))
    record['sha256'] = canonical_sha256(record)
    import json
    SubmissionStore._write_atomic_new(folder / f'{record["sequence"]:06d}.json', json.dumps(record, ensure_ascii=False, indent=2).encode())
    return record


def event(decision, kind, timestamp, suffix='', **extra):
    common = {key:decision[key] for key in ('assessment_id','participant_id','submission_id','question_attempt_id',
        'transcription_version_id','audit_run_id','human_decision_id','engine_mode','engine_version','adjustment_delta')}
    return dict(**common, event_id=f'{decision["human_decision_id"]}:{kind}:{suffix}', event_type=kind,
        timestamp=timestamp, suggested_score=decision['suggested_points'], final_score=decision['final_points'], **extra)


def append_current(case, chain, kind, decision, request, user):
    """Serialize publication against generic transcription/audit endpoints too.

    Callers hold the question and exam locks. Only unlocked store readers may
    be used here: public readers would acquire another flock on the same file.
    """
    from confia_lean_auditor.submissions.router import store as submission_store
    from confia_lean_auditor.submission_audits.router import service as audit_service
    submissions, audits = submission_store(), audit_service()
    tid, revision = decision.transcription_version_id.split(':')
    with submissions._locked(exclusive=True):
        history = submissions._transcription_history(tid)
        if history.transcription.submission_id != case.submission_id or history.revisions[-1].revision_number != int(revision):
            raise ExamConflict('reading changed before decision publication')
        folder = submissions._transcriptions_folder(case.submission_id)
        for other in folder.iterdir():
            if other.is_dir() and not other.is_symlink() and submissions._transcription_name_valid(other.name):
                if submissions._read_transcription_record(other).created_at > history.transcription.created_at:
                    raise ExamConflict('reading changed before decision publication')
        if audits.root.is_symlink(): raise ExamConflict('invalid audit directory')
        runs = [audits._read(path.stem) for path in audits.root.glob('aud_*.json')]
        current = sorted((r for r in runs if r.submission_id == case.submission_id
            and r.transcription_id == tid and r.revision_number == int(revision)),
            key=lambda r:r.created_at, reverse=True)
        if not current or current[0].audit_run_id != decision.audit_run_id:
            raise ExamConflict('audit changed before decision publication')
        return append(case, chain, kind, decision, request, user)


def project(case, runs, versions):
    chain = records(case)
    decisions = [r['decision'] for r in chain if r['kind']=='confirm']
    current_run = next((r for r in runs if not r.stale), None)
    current_version = next((v['version_id'] for v in versions if v['current']), None)
    current, history, events = None, [], []
    for index, decision in enumerate(decisions):
        did = decision['human_decision_id']
        timestamp = decision['decided_at']
        delta = Decimal(decision['adjustment_delta'])
        events.append(event(decision, 'score_adjusted' if delta else 'suggestion_accepted', timestamp))
        if delta: events.append(event(decision, 'adjustment_reason_recorded', timestamp, reason=decision['override_reason']))
        events.append(event(decision, 'question_confirmed', timestamp))
        transitions = []
        for record in chain:
            if record['kind']=='reopen' and record['decision']['human_decision_id']==did:
                transitions.append((record['timestamp'], 'REOPENED'))
                events.append(event(decision, 'question_reopened', record['timestamp'], actor_id=record['actor_id']))
        # Earliest later reading/audit, not the latest, keeps invalidation IDs stable.
        later_versions = [v for v in versions if v['created_at'] > datetime.fromisoformat(timestamp.replace("Z", "+00:00")) and v['version_id'] != decision['transcription_version_id']]
        if later_versions:
            v = min(later_versions, key=lambda v:v['created_at'])
            transitions.append((v['created_at'].isoformat(), 'INVALIDATED_BY_TRANSCRIPTION'))
            events.append(event(decision,'confirmation_invalidated_by_transcription_change',v['created_at'].isoformat(),v['version_id'], new_transcription_version_id=v['version_id']))
        later_runs = [r for r in runs if r.audit_run_id != decision['audit_run_id'] and (r.completed_at or r.created_at) > datetime.fromisoformat(timestamp.replace("Z", "+00:00"))]
        if later_runs:
            r = min(later_runs, key=lambda r:r.completed_at or r.created_at)
            transitions.append(((r.completed_at or r.created_at).isoformat(), 'INVALIDATED_BY_NEW_AUDIT'))
            events.append(event(decision,'confirmation_invalidated_by_new_audit',(r.completed_at or r.created_at).isoformat(),r.audit_run_id,new_audit_run_id=r.audit_run_id))
        if index+1 < len(decisions):
            successor=decisions[index+1]
            events.append(event(decision,'human_decision_superseded',successor['decided_at'],successor['human_decision_id'],superseded_by=successor['human_decision_id']))
        active = index == len(decisions)-1 and not transitions and current_run is not None and current_run.audit_run_id==decision['audit_run_id'] and current_version==decision['transcription_version_id']
        state = 'CONFIRMED' if active else 'SUPERSEDED' if index+1 < len(decisions) else min(transitions)[1] if transitions else 'INVALIDATED'
        row = dict(**decision, current=active, effective_status=state,
            certification=dict(human_final_score=decision['final_points'],confia_suggested_score=decision['suggested_points'],
                signed_error=str(-delta),absolute_error=str(abs(delta)),adjustment=str(delta),
                review_required=decision['review_required_snapshot'],audit_run_id=decision['audit_run_id'],engine_version=decision['engine_version']))
        history.append(row)
        if active: current=row
    return dict(current_human_decision=current, human_decisions=list(reversed(history)), human_decision_events=events,
        last_human_decision_id=decisions[-1]['human_decision_id'] if decisions else None)


def decide(case_id, body, user):
    from .question_review import workspace, owned_case
    from confia_lean_auditor.submission_audits.router import service as audit_service
    with question_lock(case_id, user):
        snapshot=workspace(case_id,user)
        with exam_store()._locked():
            case=owned_case(case_id,user)
            chain=records(case)
            replay=next((r for r in chain if r['execution_key']==body.execution_key), None)
            if replay:
                if replay['kind']!='confirm' or replay['request_sha256']!=canonical_sha256(body.model_dump(mode='json')):
                    raise ExamConflict('decision request key already used')
                return HumanDecision.model_validate(replay['decision'])
            # Recheck revision under exam lock: edits may have followed snapshot.
            from confia_lean_auditor.submissions.router import store as submission_store
            readings=submission_store().list_transcriptions(case.submission_id) if case.submission_id else []
            version=f'{readings[0].transcription.transcription_id}:{readings[0].latest_revision.revision_number}' if readings else None
            audit=snapshot['current_audit']
            if (version != body.transcription_version_id or not audit or audit['audit_run_id']!=body.audit_run_id
                    or audit['transcription_version_id']!=version or audit['status']!='COMPLETED' or audit['suggested_score'] is None):
                raise ExamConflict('audit no longer current or scorable')
            if snapshot['current_human_decision'] or snapshot['last_human_decision_id'] != body.expected_last_decision_id:
                raise ExamConflict('human decision changed; reopen before confirming')
            suggested=Decimal(str(audit['suggested_score']))
            final=suggested if body.decision_type=='ACCEPT_SUGGESTION' else body.final_points
            if final is None or (body.decision_type=='ACCEPT_SUGGESTION' and body.final_points is not None and body.final_points!=suggested):
                raise ValueError('invalid final score')
            raw=audit_service().get(body.audit_run_id)
            decision=HumanDecision(human_decision_id='hdec_'+uuid4().hex,case_id=case_id,question_attempt_id=case_id,
                assessment_id=audit['assessment_id'],participant_id=audit['participant_id'],submission_id=case.exam_submission_id,
                transcription_version_id=version,audit_run_id=raw.audit_run_id,audit_source_sha256=raw.source_hash,audit_result_sha256=raw.result_sha256,
                max_points=case.max_score,suggested_points=suggested,final_points=final,adjustment_delta=final-suggested,
                override_reason=(body.override_reason or '').strip() or None,decision_type=body.decision_type,
                decided_by_user_id=user.user_id,decided_at=datetime.now(timezone.utc),engine_mode=audit['engine_mode'],engine_version=audit['engine_version'],
                review_required_snapshot=audit['review_required'],review_reasons_snapshot=audit['review_reasons'],supersedes_decision_id=body.expected_last_decision_id)
            append_current(case,chain,'confirm',decision,body,user)
            return decision


def reopen(case_id, body, user):
    from .question_review import workspace, owned_case
    with question_lock(case_id,user):
        snapshot=workspace(case_id,user)
        with exam_store()._locked():
            case=owned_case(case_id,user); chain=records(case)
            replay=next((r for r in chain if r['execution_key']==body.execution_key),None)
            if replay:
                if replay['kind']!='reopen' or replay['request_sha256']!=canonical_sha256(body.model_dump(mode='json')):raise ExamConflict('request key already used')
                return {'reopened_decision_id':body.human_decision_id}
            current=snapshot['current_human_decision']
            if not current or current['human_decision_id']!=body.human_decision_id:raise ExamConflict('confirmation no longer current')
            from confia_lean_auditor.submissions.router import store as submission_store
            readings=submission_store().list_transcriptions(case.submission_id)
            version=f'{readings[0].transcription.transcription_id}:{readings[0].latest_revision.revision_number}' if readings else None
            if version != current['transcription_version_id']: raise ExamConflict('reading changed before reopening')
            decision=HumanDecision.model_validate({k:v for k,v in current.items() if k in HumanDecision.model_fields})
            append_current(case,chain,'reopen',decision,body,user)
            return {'reopened_decision_id':body.human_decision_id}
