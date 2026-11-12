"""Plain-text originals in the existing submission/receipt/transcription store."""

import os
import shutil
import tempfile
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import Field
from typing import Literal
from .schemas import (
    SubmissionModel,
    SubmissionRecord,
    SubmissionReceipt,
    ArtifactReference,
)
from hashlib import sha256 as _sha256


def sha256(data):
    return _sha256(data).hexdigest()


class TextSnapshot(SubmissionModel):
    schema_version: Literal["text-source.v1"] = "text-source.v1"
    snapshot_id: str
    problem_id: str
    case_id: str
    text: str = Field(min_length=1, max_length=20000)


def receive_text(store, case, user, text):
    from confia_lean_auditor.dynamic.grading_context import case_context

    if (
        not case.dynamic_context
        or case.created_by_user_id != user.user_id
        or case.source_mode != "TEXT"
    ):
        raise ValueError("invalid text case")
    case_context(case)
    snapshot = TextSnapshot(
        snapshot_id="text:" + uuid4().hex,
        problem_id=case.problem_id,
        case_id=case.case_id,
        text=text,
    )
    raw = snapshot.model_dump_json().encode()
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
        submitted_by_user_id=user.user_id,
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
            store._sync_directory(pending)
            os.replace(pending, store.root / record.submission_id)
            store._sync_directory(store.root)
        finally:
            if pending.exists():
                shutil.rmtree(pending)
    return receipt
