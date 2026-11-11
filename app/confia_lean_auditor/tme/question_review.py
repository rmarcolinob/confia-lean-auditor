"""Question workspace over the existing immutable submission/transcription stores.

Lock order: exam -> submissions (released) -> case. GET never creates a source,
transcription or event. Events are stable projections of immutable records.
"""
from datetime import datetime, timezone
from uuid import uuid4

from confia_lean_auditor.submissions.router import store as submission_store
from confia_lean_auditor.submissions.schemas import (
    CreateTranscriptionRequest, TranscriptionRecord, TranscriptionRevision,
    TranscriptionSegment, CaptureImportProvenance,
)
from confia_lean_auditor.submissions.store import TranscriptionConflict
from confia_lean_auditor.submission_audits.router import service as audit_service
from .correction_engine import project_audit, review_reasons
from .exam_store import exam_store, ExamConflict
from .store import case_store
from .review_models import QuestionSourceSnapshot, QuestionSourcePage


def owned_case(case_id, user):
    case = case_store().for_user(case_id, user)
    if not case.exam_submission_id:
        raise FileNotFoundError()
    return case


def mapped_pages(detail, case_id):
    pages = {p.exam_page_id: p for p in detail.submission.pages}
    return [pages[b.exam_page_id] for b in sorted(detail.mapping.bindings, key=lambda b: b.order)
            if b.question_attempt_id == case_id]


def snapshot_for(detail, case):
    assets = {a.asset_id: a for a in [*detail.submission.original_documents, *detail.submission.previews]}
    pages = mapped_pages(detail, case.case_id)
    if not pages:
        raise ExamConflict("associate pages before transcribing")
    return QuestionSourceSnapshot(snapshot_id=f"exam-question:{case.case_id}", question_attempt_id=case.case_id,
        exam_submission_id=case.exam_submission_id, problem_id=case.problem_id, mapping_version=detail.mapping.version,
        pages=[QuestionSourcePage(index=i, page_id=p.exam_page_id, exam_page=p,
            original=assets[p.original_asset_id], preview=assets[p.preview_asset_id],
            derived_width=p.width, derived_height=p.height) for i, p in enumerate(pages)])


def freeze_source(exams, detail, case, user):
    """Caller owns exam lock, including until case binding completes."""
    source = snapshot_for(detail, case)
    folder = exams.folder(case.exam_submission_id)
    # Verify assets against the immutable manifest without reacquiring exam lock.
    from hashlib import sha256
    previews = []
    for page in source.pages:
        for ref in (page.original, page.preview):
            path = folder / ref.asset_id
            if path.is_symlink():
                raise ExamConflict("invalid asset path")
            data = path.read_bytes()
            if len(data) != ref.byte_size or sha256(data).hexdigest() != ref.sha256:
                raise ExamConflict("asset integrity mismatch")
            if ref == page.preview:
                previews.append(data)
    record = submission_store().receive_exam_question(source, previews, user)
    if case.submission_id and case.submission_id != record.submission_id:
        raise ExamConflict("different source already bound")
    return case_store().bind(case.case_id, record.submission_id, user)


def capture_segments(detail, case):
    hints = {h.page_number: h for h in detail.submission.capture_pages}
    segments, ids = [], []
    for index, page in enumerate(mapped_pages(detail, case.case_id)):
        hint = hints.get(page.page_number)
        # A candidate explicitly attributed to another question is never imported.
        if not hint or not hint.transcription_candidate or (hint.question_hint and hint.question_hint != case.problem_id):
            continue
        segments.append(TranscriptionSegment(segment_id=f"capture:{page.exam_page_id}", page_index=index,
            order=0, kind="mixed", text=hint.transcription_candidate, confidence=hint.confidence))
        ids.append(page.exam_page_id)
    return segments, ids


def create(case_id, request, user):
    case, exams = owned_case(case_id, user), exam_store()
    with exams._locked():
        detail = exams._detail(case.exam_submission_id, user)
        from .finalization import assert_editable
        assert_editable(case.exam_submission_id)
        case = next(c for c in detail.question_attempts if c.case_id == case_id)
        if request.expected_mapping_version != detail.mapping.version:
            raise ExamConflict("mapping changed before import")
        if case.status == "DECIDED":
            raise ExamConflict("question already confirmed")
        segments, page_ids = capture_segments(detail, case) if request.origin == "capture" else (request.segments, [])
        if not segments or any(not (s.text or s.latex or "").strip() for s in segments):
            raise ValueError("no transcription content")
        if any(s.page_index >= len(mapped_pages(detail, case_id)) for s in segments):
            raise ValueError("segment outside question")
        case = freeze_source(exams, detail, case, user)
        store = submission_store()
        if store.list_transcriptions(case.submission_id):
            raise TranscriptionConflict("initial transcription already exists")
        if request.origin == "manual":
            return store.create_transcription(case.submission_id, CreateTranscriptionRequest(
                reviewer_reference=user.user_id, segments=segments))
        with store._locked(exclusive=True):
            record = TranscriptionRecord(transcription_id="tr_" + uuid4().hex, submission_id=case.submission_id,
                created_at=datetime.now(timezone.utc), source="capture", capture_origin=CaptureImportProvenance(
                    exam_submission_id=case.exam_submission_id,
                    producer=detail.submission.capture_metadata.producer,
                    producer_version=detail.submission.capture_metadata.producer_version, page_ids=page_ids))
            revision = TranscriptionRevision(**record.model_dump(), revision_number=1,
                reviewer_reference=user.user_id, change_type="initial_transcription",
                segments=segments, status="NEEDS_REVIEW")
            return store._publish_transcription(record, revision)


def revise(case_id, transcription_id, request, user):
    case, exams = owned_case(case_id, user), exam_store()
    with exams._locked():
        detail = exams._detail(case.exam_submission_id, user)
        from .finalization import assert_editable
        assert_editable(case.exam_submission_id)
        case = next(c for c in detail.question_attempts if c.case_id == case_id)
        histories = submission_store().list_transcriptions(case.submission_id)
        if case.status == "DECIDED" or not histories or histories[0].transcription.transcription_id != transcription_id:
            raise TranscriptionConflict("only the current question reading is editable")
        if any(not (s.text or s.latex or "").strip() for s in request.segments):
            raise ValueError("empty corrected text")
        return submission_store().create_transcription_revision(transcription_id, request)


def recognize(case_id, request, user, registry):
    """Same RecognitionService/provider; no alternative OCR implementation."""
    from confia_lean_auditor.recognition.service import RecognitionService
    case, exams = owned_case(case_id, user), exam_store()
    with exams._locked():
        detail = exams._detail(case.exam_submission_id, user)
        from .finalization import assert_editable
        assert_editable(case.exam_submission_id)
        case = next(c for c in detail.question_attempts if c.case_id == case_id)
        if case.status == "DECIDED":
            raise ExamConflict("confirmed question")
        case = freeze_source(exams, detail, case, user)
        if submission_store().list_transcriptions(case.submission_id):
            raise TranscriptionConflict("preserve the existing reading; correct it through revisions")
        # Serialize first publication against manual/capture imports and mapping.
        return RecognitionService(submission_store(), registry).recognize(case.submission_id, request)


def version_view(revision, pages, *, current):
    origin = ("human" if revision.revision_number > 1 or revision.source == "manual" else
              "capture" if revision.source == "capture" else "digital_ink" if revision.provenance and
              revision.provenance.input_mode == "strokes" else "automatic")
    tid, number = revision.transcription_id, revision.revision_number
    return dict(version_id=f"{tid}:{number}", question_attempt_id=None, version_number=number,
        predecessor_version_id=f"{tid}:{number-1}" if number > 1 else None,
        origin=origin, created_at=revision.created_at, created_by=revision.reviewer_reference,
        current=current, text="\n\n".join(s.text or s.latex or "" for s in sorted(revision.segments, key=lambda s:(s.page_index,s.order))),
        segments=[dict(segment=s.model_dump(mode="json"), exam_page_id=pages[s.page_index].exam_page_id,
                       page_number=pages[s.page_index].page_number) for s in revision.segments])


def question_state(case, has_reading, runs):
    if case.status == "DECIDED":
        return "CONFIRMED"
    if not has_reading:
        return "PENDING"
    current = next((r for r in runs if not r.stale), None)
    if current and current.status == "COMPLETED" and current.result and not review_reasons(current):
        return "READY"
    return "REVIEW"


def workspace(case_id, user):
    case, exams = owned_case(case_id, user), exam_store()
    with exams._locked():
        detail = exams._detail(case.exam_submission_id, user)
        case = next(c for c in detail.question_attempts if c.case_id == case_id)
        pages = mapped_pages(detail, case_id)
        store = submission_store()
        summaries = store.list_transcriptions(case.submission_id) if case.submission_id else []
        history = store.transcription_history(summaries[0].transcription.transcription_id) if summaries else None
        if case.submission_id:
            record = store.assert_submission_integrity(case.submission_id)
            source = QuestionSourceSnapshot.model_validate_json((store._folder(record.submission_id) / "snapshot.json").read_bytes())
            expected = snapshot_for(detail, case)
            if source.model_dump(exclude={"mapping_version"}) != expected.model_dump(exclude={"mapping_version"}):
                raise ExamConflict("frozen source does not match question")
        runs = audit_service().list(case.submission_id) if case.submission_id else []
        current_run = next((r for r in runs if not r.stale), None)
        completed_current = current_run and current_run.status == "COMPLETED"
        audit_stale = bool(not current_run and any(r.stale for r in runs))
        human = bool(history and any(r.revision_number > 1 for r in history.revisions))
        reanalysis = bool(not completed_current and (human or audit_stale))
        state = question_state(case, bool(history), runs)
        versions, events = [], []
        for summary in reversed(summaries):
            chain = store.transcription_history(summary.transcription.transcription_id)
            for revision in chain.revisions:
                current = bool(history and revision.transcription_id == history.transcription.transcription_id and revision.revision_number == history.revisions[-1].revision_number)
                version = version_view(revision, pages, current=current)
                version["question_attempt_id"] = case_id
                versions.append(version)
                for event_type in (["transcription_created"] if revision.revision_number == 1 else ["transcription_human_corrected"]) + ["transcription_activated"]:
                    events.append(dict(event_id=f'{version["version_id"]}:{event_type}', event_type=event_type,
                        question_attempt_id=case_id, transcription_version_id=version["version_id"],
                        created_at=revision.created_at, created_by=revision.reviewer_reference))
        for run in runs:
            if run.stale and versions:
                # First later activation that superseded this source, stable across subsequent edits.
                replacement = next((v for v in versions if v["created_at"] > run.source.provenance.revision.created_at and
                    v["version_id"] != f"{run.transcription_id}:{run.revision_number}"), versions[-1])
                events.append(dict(event_id=f'{run.audit_run_id}:stale:{replacement["version_id"]}',
                    event_type="audit_marked_stale", question_attempt_id=case_id,
                    transcription_version_id=replacement["version_id"], audit_run_id=run.audit_run_id,
                    created_at=max(run.created_at,replacement["created_at"])))
        # Enrich the existing immutable-revision projections, without writing on GET.
        for event in events:
            prior = next((r for r in runs if r.created_at <= event["created_at"] and
                f"{r.transcription_id}:{r.revision_number}" != event["transcription_version_id"]), None)
            linked = next((r for r in runs if r.audit_run_id == event.get("audit_run_id")), prior)
            event.update(assessment_id=detail.submission.assessment_id,
                participant_id=detail.submission.participant_id, submission_id=case.exam_submission_id,
                timestamp=event["created_at"], engine_version=getattr(linked, "auditor_version", None),
                previous_audit_run_id=linked.audit_run_id if linked else None)
        from .human_decisions import project as project_human
        human_data = project_human(case, runs, versions)
        if human_data["current_human_decision"]: state = "CONFIRMED"
        human_current = {case_id: human_data["current_human_decision"]}
        question_states = {}
        all_runs = {case_id: runs}
        for sibling in detail.question_attempts:
            if sibling.case_id == case_id:
                question_states[sibling.case_id] = state
                continue
            readings = store.list_transcriptions(sibling.submission_id) if sibling.submission_id else []
            sibling_runs = audit_service().list(sibling.submission_id) if sibling.submission_id and readings else []
            question_states[sibling.case_id] = question_state(sibling, bool(readings), sibling_runs)
            all_runs[sibling.case_id] = sibling_runs
            sibling_versions = []
            for summary in readings:
                for revision in store.transcription_history(summary.transcription.transcription_id).revisions:
                    sibling_versions.append(dict(version_id=f'{revision.transcription_id}:{revision.revision_number}',
                        created_at=revision.created_at,current=summary==readings[0] and revision.revision_number==summary.latest_revision.revision_number))
            sibling_human = project_human(sibling, sibling_runs, sibling_versions)
            human_current[sibling.case_id] = sibling_human["current_human_decision"]
            if sibling_human["current_human_decision"]: question_states[sibling.case_id] = "CONFIRMED"
        segments, _ = capture_segments(detail, case)
        audits = [project_audit(run, case, detail) for run in runs]
        current_audit = next((r for r in audits if not r["stale"]), None)
        previous_audit = next((r for r in audits if r["stale"]), None)
        from decimal import Decimal
        current_runs = [next((r for r in all_runs[c.case_id] if not r.stale), None) for c in detail.question_attempts]
        scored = [r for r in current_runs if r and r.status == "COMPLETED" and r.result and r.result.score is not None]
        partial = dict(suggested_score=float(sum((Decimal(str(r.result.score)) for r in scored), Decimal(0))),
            max_score=float(sum(c.max_score for c in detail.question_attempts)),
            analyzed_questions=len(scored), total_questions=len(detail.question_attempts),
            awaiting_reanalysis=sum((not current or current.status == "FAILED") and any(r.stale for r in all_runs[c.case_id])
                for c, current in zip(detail.question_attempts, current_runs)),
            complete=len(scored) == len(detail.question_attempts))
        confirmed = [d for d in human_current.values() if d]
        confirmed_total = dict(final_score=str(sum((Decimal(d["final_points"]) for d in confirmed), Decimal(0))),
            max_score=str(sum((Decimal(d["max_points"]) for d in confirmed), Decimal(0))),
            exam_max_score=partial["max_score"], confirmed_questions=len(confirmed),
            total_questions=len(detail.question_attempts), remaining_questions=len(detail.question_attempts)-len(confirmed))
        from .finalization import lifecycle
        closure = lifecycle(case.exam_submission_id)
        return dict(exam_finalized=bool(closure['current_final_correction']), **human_data, confirmed_total=confirmed_total, question_decisions=human_current,
            question_attempt=case, pages=pages, mapping_version=detail.mapping.version,
            history=history, versions=versions, question_states=question_states, current_version=next((v for v in versions if v["current"]), None),
            state=state, human_reviewed=human, audit_stale=audit_stale, reanalysis_required=reanalysis,
            analysis_state="FAILED" if current_run and current_run.status == "FAILED" else "REANALYSIS_REQUIRED" if reanalysis else "AVAILABLE" if current_run else "AWAITING_ANALYSIS",
            capture_candidate_available=bool(segments) and history is None,
            audits=audits, current_audit=current_audit, previous_audit=previous_audit,
            audit_comparison=current_audit.get("comparison") if current_audit else None, partial_suggestion=partial,
            events=events + [event for run in audits for event in run["events"]] + human_data["human_decision_events"])
