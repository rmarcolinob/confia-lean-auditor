"""Full-exam envelope around existing Assessment, participant and CorrectionCase.

Immutable capture manifests and assets; append-only page mappings. No OCR/auditor
is invoked. Deterministic child IDs recover an interrupted publication on retry.
"""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from uuid import uuid4

from fastapi import HTTPException

from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.assessments.models import AssessmentDocument, AssessmentParticipant
from confia_lean_auditor.assessments.store import AssessmentStore, assessment_store
from confia_lean_auditor.assessments.participants import participant_store
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.submissions.store import SubmissionStore
from .store import case_store
from .models import CaseCreate
from .exam_models import ExamAsset, ExamPage, ExamSubmission, ExamDetail, PageMapping, QuestionAttemptView
from .exam_capture import prepare


class ExamConflict(ValueError):
    pass


def exam_store():
    configured = os.environ.get("CONFIA_TME_EXAMS_DIR")
    return ExamStore(Path(configured).resolve() if configured else get_repo_root() / "runtime/tme_exams")


def tme_assessment(identifier, user):
    doc = assessment_store().get(identifier)
    if doc.assessment.scope != "TME" or doc.assessment.teacher_user_id != user.user_id:
        raise HTTPException(403, "Avaliação fora do escopo do avaliador.")
    if doc.assessment.status != "PUBLISHED":
        raise ExamConflict("A avaliação não está disponível para recebimento.")
    return doc


def sealed(value):
    return {"data": value, "sha256": canonical_sha256(value)}


def read_sealed(path):
    if path.is_symlink():
        raise ExamConflict("Referência de armazenamento inválida.")
    raw = json.loads(path.read_bytes())
    if raw.get("sha256") != canonical_sha256(raw.get("data")):
        raise ExamConflict("A integridade da prova não confere.")
    return raw["data"]


class ExamStore(AssessmentStore):
    def folder(self, identifier):
        if not re.fullmatch(r"exam_[0-9a-f]{32}", identifier) or self.root.is_symlink():
            raise FileNotFoundError()
        path = self.root / identifier
        if path.is_symlink() or not path.is_dir():
            raise FileNotFoundError()
        return path

    def _manifest(self, identifier, user):
        raw = read_sealed(self.folder(identifier) / "exam.json")
        submission = ExamSubmission.model_validate(raw["submission"])
        if submission.created_by_user_id != user.user_id:
            raise HTTPException(403, "Prova fora do escopo do avaliador.")
        assessment = AssessmentDocument.model_validate(raw["assessment"])
        participant = AssessmentParticipant.model_validate(raw["participant"])
        from confia_lean_auditor.assessments.store import definition_hash
        if (submission.submission_id != identifier or submission.assessment_id != assessment.assessment.assessment_id
                or submission.assessment_definition_sha256 != definition_hash(assessment)
                or participant.assessment_id != submission.assessment_id
                or submission.participant_id != participant.participant_id
                or len(submission.pages) != submission.page_count
                or [p.page_number for p in submission.pages] != list(range(1, submission.page_count + 1))
                or any(p.submission_id != identifier for p in submission.pages)):
            raise ExamConflict("Vínculos da prova inválidos.")
        return submission, assessment, participant

    def _mapping(self, identifier, submission):
        files = sorted(self.folder(identifier).glob("mapping_*.json"))
        if not files:
            raise ExamConflict("Associação de páginas indisponível.")
        mapping = PageMapping.model_validate(read_sealed(files[-1]))
        if files[-1].name != f"mapping_{mapping.version:06d}.json":
            raise ExamConflict("Versão de associação inválida.")
        self.validate_bindings(submission, mapping.bindings)
        return mapping

    @staticmethod
    def validate_bindings(submission, bindings):
        pages = {p.exam_page_id for p in submission.pages}
        cases = set(submission.question_attempt_ids)
        seen, orders = set(), {}
        for binding in bindings:
            key = (binding.question_attempt_id, binding.exam_page_id)
            if key in seen or binding.question_attempt_id not in cases or binding.exam_page_id not in pages:
                raise ExamConflict("Associação duplicada ou fora desta prova.")
            seen.add(key)
            orders.setdefault(binding.question_attempt_id, []).append(binding.order)
        if any(sorted(values) != list(range(1, len(values) + 1)) for values in orders.values()):
            raise ExamConflict("A ordem das páginas da questão deve ser contínua.")

    def _detail(self, identifier, user):
        submission, assessment, participant = self._manifest(identifier, user)
        attempts = [case_store().for_user(c, user) for c in submission.question_attempt_ids]
        if len(attempts) != len(assessment.items):
            raise ExamConflict("Conjunto de questões incompleto.")
        for attempt, item in zip(attempts, assessment.items):
            if (attempt.exam_submission_id != identifier or attempt.assessment_item_id != item.assessment_item_id
                    or attempt.problem_id != item.problem_id or attempt.question_order != item.order
                    or attempt.max_score != Decimal(str(item.points))):
                raise ExamConflict("Questão não corresponde à definição da prova.")
        from .finalization import lifecycle
        life = lifecycle(identifier)
        current = life["current_final_correction"]
        return ExamDetail(correction_status="FINALIZED" if current else "REOPENED" if life["reopened"] else "IN_PROGRESS",
                          current_final_correction_id=current["final_correction_id"] if current else None,
                          submission=submission, assessment=assessment, participant=participant,
                          question_attempts=attempts, mapping=self._mapping(identifier, submission))

    def detail(self, identifier, user):
        with self._locked():
            return self._detail(identifier, user)

    def list_for(self, user):
        with self._locked():
            result = []
            for path in self.root.glob("exam_*"):
                try:
                    submission, assessment, participant = self._manifest(path.name, user)
                except HTTPException as exc:
                    if exc.status_code == 403:
                        continue
                    raise
                from .finalization import lifecycle
                closure = lifecycle(submission.submission_id)
                current = closure['current_final_correction']
                result.append(dict(status='FINALIZED' if current else 'REOPENED' if closure['reopened'] else 'IN_PROGRESS',
                    final_total=current['final_total'] if current else None,
                    adjusted_question_count=current['adjusted_question_count'] if current else None,
                    finalized_at=current['finalized_at'] if current else None, submission_id=submission.submission_id, title=assessment.assessment.title,
                    participant_code=participant.external_code, page_count=submission.page_count,
                    question_count=len(submission.question_attempt_ids), created_at=submission.created_at))
            return sorted(result, key=lambda r: r["created_at"], reverse=True)

    def receive(self, package, user):
        identity = hashlib.sha256(f"{user.user_id}:{package.idempotency_key}".encode()).hexdigest()[:32]
        identifier = "exam_" + identity
        request_hash = canonical_sha256(package.model_dump(mode="json"))
        with self._locked():
            if (self.root / identifier).exists():
                previous = self._detail(identifier, user)
                if previous.submission.request_sha256 != request_hash:
                    raise ExamConflict("A chave de envio já foi usada com outro conteúdo.")
                return previous, False
            assessment = tme_assessment(package.assessment_identifier, user)
            originals, rendered = prepare(package)
            participant = participant_store().get_or_create(package.assessment_identifier, "EXTERNAL_PSEUDONYM",
                external_namespace=package.external_namespace, external_code=package.external_participant_code)
            now = datetime.now(timezone.utc)
            assets = [ExamAsset(asset_id=f"original_{i:04d}", media_type=doc.media_type,
                sha256=hashlib.sha256(data).hexdigest(), byte_size=len(data))
                for i, (doc, data) in enumerate(zip(package.original_documents, originals), 1)]
            previews, pages = [], []
            for i, (original_index, original_page, data, width, height, rotation, transformation) in enumerate(rendered, 1):
                previews.append(ExamAsset(asset_id=f"preview_{i:04d}", media_type="image/png",
                    sha256=hashlib.sha256(data).hexdigest(), byte_size=len(data)))
                pages.append(ExamPage(exam_page_id="page_" + uuid4().hex, submission_id=identifier,
                    page_number=i, original_asset_id=assets[original_index].asset_id,
                    original_page_number=original_page, preview_asset_id=previews[-1].asset_id,
                    width=width, height=height, rotation_degrees=rotation, transformation=transformation))
            cases = ["case_" + hashlib.sha256(f"{identifier}:{item.assessment_item_id}".encode()).hexdigest()[:32]
                     for item in assessment.items]
            submission = ExamSubmission(submission_id=identifier, assessment_id=package.assessment_identifier,
                assessment_definition_sha256=assessment.assessment.definition_sha256,
                participant_id=participant.participant_id, created_by_user_id=user.user_id, created_at=now,
                source="PDF" if assets[0].media_type == "application/pdf" else "IMAGES", page_count=len(pages),
                capture_metadata=package.capture_metadata, capture_pages=package.pages,
                original_documents=assets, previews=previews, pages=pages, question_attempt_ids=cases,
                request_sha256=request_hash)
            pending = Path(tempfile.mkdtemp(prefix=".pending-", dir=self.root))
            try:
                for ref, data in zip(assets, originals):
                    SubmissionStore._write(pending / ref.asset_id, data)
                for ref, render in zip(previews, rendered):
                    SubmissionStore._write(pending / ref.asset_id, render[2])
                manifest = dict(submission=submission.model_dump(mode="json"),
                    assessment=assessment.model_dump(mode="json"), participant=participant.model_dump(mode="json"))
                SubmissionStore._write(pending / "exam.json", json.dumps(sealed(manifest)).encode())
                mapping = PageMapping(version=1, updated_at=now, updated_by=user.user_id)
                SubmissionStore._write(pending / "mapping_000001.json", json.dumps(sealed(mapping.model_dump(mode="json"))).encode())
                # Child records use the existing store and deterministic IDs. A
                # crash before publication is retryable without duplicate cases.
                for case_id, item in zip(cases, assessment.items):
                    case_store().create(CaseCreate(problem_id=item.problem_id,
                        external_candidate_ref=package.external_participant_code, source_mode="IMAGE_SCAN"), user,
                        case_id=case_id, exam_binding=dict(exam_submission_id=identifier,
                            assessment_item_id=item.assessment_item_id, question_order=item.order, max_score=item.points))
                SubmissionStore._sync_directory(pending)
                os.replace(pending, self.root / identifier)
                SubmissionStore._sync_directory(self.root)
            finally:
                if pending.exists():
                    shutil.rmtree(pending)
            return self._detail(identifier, user), True

    def update_mapping(self, identifier, request, user):
        with self._locked():
            detail = self._detail(identifier, user)
            from .finalization import assert_editable
            assert_editable(identifier)
            if request.expected_version != detail.mapping.version:
                raise ExamConflict("A associação mudou. Recarregue a prova antes de salvar.")
            self.validate_bindings(detail.submission, request.bindings)
            for attempt in detail.question_attempts:
                old = [b for b in detail.mapping.bindings if b.question_attempt_id == attempt.case_id]
                new = [b for b in request.bindings if b.question_attempt_id == attempt.case_id]
                if old != new and (attempt.submission_id or attempt.status == "DECIDED"):
                    raise ExamConflict("A questão já possui fonte congelada; a associação não pode ser alterada.")
            if request.bindings == detail.mapping.bindings:
                return detail.mapping
            mapping = PageMapping(version=detail.mapping.version + 1, bindings=request.bindings,
                updated_at=datetime.now(timezone.utc), updated_by=user.user_id)
            path = self.folder(identifier) / f"mapping_{mapping.version:06d}.json"
            SubmissionStore._write_atomic_new(path, json.dumps(sealed(mapping.model_dump(mode="json"))).encode())
            return mapping

    def question(self, identifier, case_id, user):
        detail = self.detail(identifier, user)
        attempt = next((c for c in detail.question_attempts if c.case_id == case_id), None)
        if attempt is None:
            raise FileNotFoundError()
        bindings = sorted((b for b in detail.mapping.bindings if b.question_attempt_id == case_id), key=lambda b: b.order)
        pages = {p.exam_page_id: p for p in detail.submission.pages}
        return QuestionAttemptView(question_attempt=attempt, pages=[pages[b.exam_page_id] for b in bindings],
                                   mapping_version=detail.mapping.version, mapping_state="READY" if bindings else "UNASSIGNED")

    def asset(self, identifier, asset_id, user):
        with self._locked():
            submission, _, _ = self._manifest(identifier, user)
            ref = next((a for a in [*submission.original_documents, *submission.previews] if a.asset_id == asset_id), None)
            if ref is None:
                raise FileNotFoundError()
            path = self.folder(identifier) / ref.asset_id
            if path.is_symlink() or not path.is_file():
                raise ExamConflict("Arquivo original ou preview indisponível.")
            data = path.read_bytes()
            if len(data) != ref.byte_size or hashlib.sha256(data).hexdigest() != ref.sha256:
                raise ExamConflict("A integridade do arquivo não confere.")
            return data, ref
