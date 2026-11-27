"""Read-only aggregate projection of existing TME/DYNAMIC confirmations.

Call only for submissions already filtered to the manager's institutional scope.
No user impersonation, new grading decision, or individual public projection.
"""
from decimal import Decimal


def decision_state(record, submissions):
    if not record.tme_case_id:
        return None
    from confia_lean_auditor.tme.store import case_store
    from confia_lean_auditor.tme.human_decisions import project
    from confia_lean_auditor.tme.finalization import lifecycle
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.dynamic.school_service import current_release

    case = case_store().read(record.tme_case_id)
    if case.submission_id != record.submission_id or case.problem_id != record.problem_id:
        raise ValueError('Question/submission binding mismatch')
    if not case.exam_submission_id:
        return None
    submissions.assert_submission_integrity(record.submission_id)
    summaries = submissions.list_transcriptions(record.submission_id)
    histories = [submissions.transcription_history(s.transcription.transcription_id) for s in summaries]
    latest = histories[0].revisions[-1] if histories else None
    version_id = f'{latest.transcription_id}:{latest.revision_number}' if latest else None
    versions = [dict(version_id=f'{v.transcription_id}:{v.revision_number}', created_at=v.created_at,
                     current=f'{v.transcription_id}:{v.revision_number}' == version_id)
                for history in histories for v in history.revisions]
    runs = service().list(record.submission_id)
    decision = project(case, runs, versions)['current_human_decision']
    if decision is None:
        return dict(finalized=False, released=False, override=False)
    final = lifecycle(case.exam_submission_id)['current_final_correction']
    included = bool(final and any(q['question_attempt_id'] == case.case_id
        and q['human_decision_id'] == decision['human_decision_id'] for q in final['questions']))
    released = included and current_release(case.exam_submission_id, final) is not None
    delta = decision.get('adjustment_delta')
    return dict(finalized=True, released=bool(released),
                override=delta is not None and Decimal(str(delta)) != 0)
