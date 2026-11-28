"""Teacher intake only: existing cases, immutable sources and audit services."""
from typing import Literal, Optional
from types import SimpleNamespace
from pydantic import Field, field_validator
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from confia_lean_auditor.submissions.schemas import SubmissionModel, CreateTranscriptionRequest
from confia_lean_auditor.submissions.text_source import receive_text, TextSnapshot
from confia_lean_auditor.submissions.router import store
from confia_lean_auditor.dynamic.router import guarded
from .auth import require_tme_evaluator
from .models import CaseCreate
from .store import case_store
from .exam_models import OriginalUpload
from .exam_capture import prepare, CaptureError

router = APIRouter()


class DirectSolution(SubmissionModel):
    problem_id: str = Field(min_length=1, max_length=100)
    external_candidate_ref: str = Field(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9._:/-]+$')
    solution: str = Field(min_length=1, max_length=20000)
    original: Optional[OriginalUpload] = None
    allow_preparation_review: bool = False
    policy_profile: Literal['FORMATIVE_LIST', 'SCHOOL_EXAM'] = 'SCHOOL_EXAM'

    @field_validator('solution')
    @classmethod
    def nonblank(cls, value):
        if not value.strip(): raise ValueError('empty solution')
        return value


def receive(body, user):
    context = None
    if body.problem_id.startswith('dyn_'):
        from confia_lean_auditor.dynamic.grading_context import resolve, evaluator_actor
        context = guarded(resolve, body.problem_id, evaluator_actor(user), body.allow_preparation_review)[0]
    original = None
    if body.original:
        try:
            originals, _ = prepare(SimpleNamespace(original_documents=[body.original], pages=[]))
        except CaptureError as error:
            raise HTTPException(422, str(error)) from None
        original = body.original.media_type, originals[0]
    case = guarded(case_store().create, CaseCreate(problem_id=body.problem_id,
        external_candidate_ref=body.external_candidate_ref, source_mode='TEXT'), user, dynamic_context=context)
    receipt = guarded(receive_text, store(), case, user, body.solution, direct=True, original=original)
    case = guarded(case_store().bind, case.case_id, receipt.submission_id, user)
    guarded(store().create_transcription, receipt.submission_id, CreateTranscriptionRequest(
        reviewer_reference=user.user_id, segments=[dict(segment_id='text:0', page_index=0,
        order=0, kind='text', text=body.solution)]))
    if context:
        from confia_lean_auditor.dynamic.reconciliation_service import configure_activity
        guarded(configure_activity, case, body.policy_profile)
    return case


@router.post('/direct-solutions', status_code=201)
async def direct_solution(request: Request, response: Response, user=Depends(require_tme_evaluator)):
    from .router import bounded_json
    raw = await bounded_json(request, 29_000_000)
    try:
        body = DirectSolution.model_validate_json(raw)
    except ValueError:
        raise HTTPException(422, "Confira problema, resolução e arquivo original.") from None
    response.headers['Cache-Control'] = 'no-store'
    return await run_in_threadpool(receive, body, user)


@router.get('/cases/{case_id}/original-document')
def original_document(case_id: str, user=Depends(require_tme_evaluator)):
    from .router import case_for
    case = case_for(case_id, user)
    if case.source_mode != 'TEXT' or not case.submission_id:
        raise HTTPException(404, 'Original não encontrado.')
    sources = store()
    with sources._locked():
        guarded(sources.assert_submission_integrity, case.submission_id)
        folder = sources.root / case.submission_id
        snapshot = TextSnapshot.model_validate_json((folder / 'snapshot.json').read_bytes())
    if not snapshot.original: raise HTTPException(404, 'Original não anexado.')
    return FileResponse(folder / 'original_1.bin', media_type=snapshot.original.media_type,
        headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
                 'Content-Security-Policy': "sandbox"})
