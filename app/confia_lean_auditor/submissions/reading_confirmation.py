"""Explicit source/scope attestation, independent of OCR and mathematical grading.

Callers authorize the actor and hold the submission lock. Existing acceptances and
revisions are never rewritten. A new revision needs a new attestation.
"""
from datetime import datetime, timezone
from typing import Literal
import json
import re
from pydantic import Field
from .schemas import SubmissionModel, Sha256
from .integrity import model_sha256, canonical_sha256
from .store import TranscriptionConflict, TranscriptionIntegrityConflict


class ConfirmReading(SubmissionModel):
    revision_number: int = Field(ge=1)
    revision_sha256: Sha256
    confirmed: Literal[True]
    question_scope_confirmed: Literal[True]


class ReadingConfirmation(SubmissionModel):
    schema_version: Literal['reading-confirmation.v1'] = 'reading-confirmation.v1'
    case_id: str
    submission_id: str
    transcription_id: str
    revision_number: int
    revision_sha256: Sha256
    source_snapshot_sha256: Sha256
    reviewer_reference: str
    confirmed_at: datetime
    question_scope_confirmed: Literal[True] = True
    page_indices: list[int]
    segment_ids: list[str]


def required(case):
    return bool(case.dynamic_context and case.source_mode == 'IMAGE_SCAN')


def unresolved(revision, page_count):
    text='\n'.join(s.text or s.latex or '' for s in revision.segments)
    return (any(i.requires_review for i in revision.input_issues)
        or any(s.kind in {'unknown','diagram'} or not (s.text or s.latex or '').strip() for s in revision.segments)
        or set(s.page_index for s in revision.segments)!=set(range(page_count))
        or bool(re.search(r'\[(?:trecho\s+)?(?:ileg[ií]vel|illegible)\]',text,re.I)))


def revision_and_source(store, case, transcription_id):
    source=store.assert_submission_integrity(case.submission_id)
    folder=store._transcription_folder(transcription_id)
    history=store._history_from_folder(folder)
    if history.transcription.submission_id!=case.submission_id:
        raise TranscriptionConflict('Leitura fora desta questão.')
    revision=store._read_revisions(folder)[-1]
    return source,revision,folder,history


def read(store, case, source, revision, folder):
    directory=folder/'reading_confirmations'
    path=directory/f'revision_{revision.revision_number:06d}.json'
    if directory.is_symlink() or path.is_symlink():raise TranscriptionIntegrityConflict()
    if not path.exists():return None
    try:
        raw=json.loads(path.read_bytes());proof=ReadingConfirmation.model_validate(raw['data'])
        if raw['sha256']!=canonical_sha256(raw['data']):raise ValueError()
        if (proof.case_id!=case.case_id or proof.submission_id!=source.submission_id
            or proof.transcription_id!=revision.transcription_id or proof.revision_number!=revision.revision_number
            or proof.revision_sha256!=model_sha256(revision) or proof.source_snapshot_sha256!=source.snapshot.sha256
            or proof.page_indices!=sorted({s.page_index for s in revision.segments})
            or proof.segment_ids!=[s.segment_id for s in revision.segments]
            or proof.reviewer_reference!=case.created_by_user_id or proof.confirmed_at.tzinfo is None):raise ValueError()
    except (ValueError,KeyError,TypeError):raise TranscriptionIntegrityConflict() from None
    return proof


def confirm(store, case, transcription_id, body, actor_id):
    source,revision,folder,_=revision_and_source(store,case,transcription_id)
    if body.revision_number!=revision.revision_number or body.revision_sha256!=model_sha256(revision):
        raise TranscriptionConflict('A leitura mudou. Confira a versão atual.')
    if unresolved(revision,len(source.page_images)):
        raise TranscriptionConflict('Resolva os trechos ilegíveis, ambíguos ou sem leitura antes de confirmar.')
    existing=read(store,case,source,revision,folder)
    if existing:return existing
    proof=ReadingConfirmation(case_id=case.case_id,submission_id=source.submission_id,
        transcription_id=transcription_id,revision_number=revision.revision_number,
        revision_sha256=model_sha256(revision),source_snapshot_sha256=source.snapshot.sha256,
        reviewer_reference=actor_id,confirmed_at=datetime.now(timezone.utc),
        page_indices=sorted({s.page_index for s in revision.segments}),segment_ids=[s.segment_id for s in revision.segments])
    data=proof.model_dump(mode='json');path=folder/'reading_confirmations'/f'revision_{revision.revision_number:06d}.json'
    store._write_atomic_new(path,json.dumps(dict(data=data,sha256=canonical_sha256(data))).encode())
    return proof


def project(store, case, transcription_id):
    source,revision,folder,history=revision_and_source(store,case,transcription_id)
    proof=read(store,case,source,revision,folder)
    pending=unresolved(revision,len(source.page_images))
    return dict(required=True,status='UNRESOLVED' if pending else 'CONFIRMED' if proof else 'NEEDS_CONFIRMATION',
        revision_number=revision.revision_number,revision_sha256=model_sha256(revision),
        technically_accepted=any(a.revision_number==revision.revision_number for a in history.acceptances),
        automatic=revision.source=='automatic' and revision.revision_number==1,
        confirmation=proof.model_dump(mode='json') if proof else None)
