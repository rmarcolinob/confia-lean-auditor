"""Plain-text originals in the existing submission/receipt/transcription store."""

import os
import shutil
import tempfile
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import Field
from typing import Literal, Optional
from .schemas import (
    SubmissionModel,
    SubmissionRecord,
    SubmissionReceipt,
    ArtifactReference,
)
from hashlib import sha256 as _sha256


def sha256(data):
    return _sha256(data).hexdigest()


DIRECT_CONFIRMATION = "Conferi explicitamente a transcrição com a solução original antes da auditoria."


class TextSnapshot(SubmissionModel):
    schema_version: Literal["text-source.v1"] = "text-source.v1"
    snapshot_id: str
    problem_id: str
    case_id: str
    text: str = Field(min_length=1, max_length=20000)
    teacher_confirmation_required: bool = False
    original: Optional[ArtifactReference] = None


def receive_text(store, case, user, text, *, direct=False, original=None):
    from confia_lean_auditor.dynamic.grading_context import case_context

    if (
        case.created_by_user_id != user.user_id
        or case.source_mode != "TEXT"
    ):
        raise ValueError("invalid text case")
    if case.dynamic_context:
        case_context(case)
    else:
        from confia_lean_auditor.core.problem_catalog import CATALOG
        from confia_lean_auditor.tme.audit_models import PUBLIC_PROBLEMS
        if case.problem_id not in CATALOG.keys() | PUBLIC_PROBLEMS.keys():
            raise ValueError("unknown prepared problem")
    snapshot = TextSnapshot(
        snapshot_id="text:" + uuid4().hex,
        problem_id=case.problem_id,
        case_id=case.case_id,
        text=text,
        teacher_confirmation_required=direct,
        original=ArtifactReference(filename="original_1.bin", media_type=original[0], sha256=sha256(original[1]), size_bytes=len(original[1])) if original else None,
    )
    raw = snapshot.model_dump_json().encode()
    from confia_lean_auditor.dynamic.school_scope import source_binding
    author_binding=source_binding(case)
    record = SubmissionRecord(
        submission_id="sub_" + uuid4().hex,
        problem_id=case.problem_id,
        snapshot_id=snapshot.snapshot_id,
        source="text",
        capture_schema_version="text-source.v1",
        received_at=datetime.now(timezone.utc),
        snapshot=ArtifactReference(
            filename="snapshot.json",
            media_type="application/json",
            sha256=sha256(raw),
            size_bytes=len(raw),
        ),
        page_images=[],
        **dict({"submitted_by_user_id":user.user_id},**author_binding),
        tenant_id=user.tenant_id,
        tme_case_id=case.case_id,
    )
    receipt = SubmissionReceipt(**record.model_dump())
    with store._locked(exclusive=True):
        pending = type(store.root)(tempfile.mkdtemp(prefix=".pending-", dir=store.root))
        try:
            for name, data in [
                ("snapshot.json", raw),
                ("submission.json", record.model_dump_json().encode()),
                ("receipt.json", receipt.model_dump_json().encode()),
            ]:
                store._write(pending / name, data)
            if original:
                store._write(pending / "original_1.bin", original[1])
            store._sync_directory(pending)
            os.replace(pending, store.root / record.submission_id)
            store._sync_directory(store.root)
        finally:
            if pending.exists():
                shutil.rmtree(pending)
    return receipt
