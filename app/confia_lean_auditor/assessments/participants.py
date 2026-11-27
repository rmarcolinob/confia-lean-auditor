"""Pseudonymous participation, independent of authentication and civil identity."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.submissions.store import SubmissionStore
from .models import AssessmentParticipant
from .store import AssessmentStore, AssessmentIntegrityConflict


def participant_store():
    root = os.environ.get("CONFIA_ASSESSMENT_PARTICIPANTS_DIR")
    return ParticipantStore(Path(root).resolve() if root else get_repo_root() / "runtime/assessment_participants")


class ParticipantStore(AssessmentStore):
    # Reuse the local repository lock; records remain append-only.
    def get_or_create(self, assessment_id, participant_kind, *, user_id=None,
                      external_namespace=None, external_code=None):
        participant = AssessmentParticipant(participant_id="part_" + "0" * 32, assessment_id=assessment_id,
            participant_kind=participant_kind, user_id=user_id, external_namespace=external_namespace,
            external_code=external_code, created_at=datetime.now(timezone.utc))
        identity = [participant.assessment_id, participant.participant_kind, participant.user_id,
                    participant.external_namespace, participant.external_code]
        identifier = "part_" + hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:32]
        participant = participant.model_copy(update={"participant_id": identifier})
        with self._locked():
            path = self.root / f"{identifier}.json"
            if path.is_symlink():
                raise AssessmentIntegrityConflict("invalid participant path")
            if path.exists():
                previous = AssessmentParticipant.model_validate_json(path.read_bytes())
                if previous.model_dump(exclude={"created_at"}) != participant.model_dump(exclude={"created_at"}):
                    raise AssessmentIntegrityConflict("participant identity mismatch")
                return previous
            SubmissionStore._write_atomic_new(path, participant.model_dump_json(indent=2).encode())
        return participant
