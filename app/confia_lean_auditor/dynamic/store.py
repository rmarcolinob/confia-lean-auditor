"""Append-only DY1 aggregates using the existing lock/hash/atomic-write primitives.

One sealed snapshot commits content and lifecycle events together. There is no
second audit/event database and no rewrite of approved content or old snapshots.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from uuid import uuid4

from confia_lean_auditor.assessments.store import AssessmentStore, AssessmentIntegrityConflict
from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.core.correction_mode import CorrectionConfiguration, PackageReference
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.submissions.integrity import canonical_sha256
from .models import model_sha256
from .preparation_models import PreparationReference
from .provider import provider_available
from .models import (DynamicDocument, DynamicProblem, StatementVersion, RubricVersion,
    DynamicProblemPackage, Approval, DynamicEvent, Provenance)


class DynamicConflict(ValueError):
    pass


def dynamic_store():
    configured = os.environ.get("CONFIA_DYNAMIC_DIR")
    return DynamicStore(Path(configured).absolute() if configured else get_repo_root() / "runtime/dynamic")


def now():
    return datetime.now(timezone.utc)


def provenance(actor):
    return Provenance(origin=actor.kind)


class DynamicStore(AssessmentStore):
    def folder(self, identifier):
        if not re.fullmatch(r"dyn_[0-9a-f]{32}", identifier):
            raise FileNotFoundError()
        path = self.root / identifier
        if path.is_symlink():
            raise AssessmentIntegrityConflict("invalid Dynamic folder")
        return path

    def _load(self, identifier):
        previous_hash, previous = None, None
        for index, path in enumerate(sorted(self.folder(identifier).glob("revision_*.json")), 1):
            try:
                if path.is_symlink() or path.name != f"revision_{index:06d}.json":
                    raise ValueError("invalid revision path")
                record = json.loads(path.read_bytes())
                digest = record.pop("sha256")
                if set(record) != {"previous_sha256", "document"} or canonical_sha256(record) != digest or record["previous_sha256"] != previous_hash:
                    raise ValueError("invalid revision chain")
                document = DynamicDocument.model_validate(record["document"])
                if document.revision != index or document.problem.problem_id != identifier:
                    raise ValueError("invalid revision identity")
                if previous:
                    if previous.problem != document.problem:
                        raise ValueError("problem ownership changed")
                    for field in ("statements", "rubrics", "packages", "approvals", "events", "preparations"):
                        old, new = getattr(previous, field), getattr(document, field)
                        if tuple(new[:len(old)]) != old:
                            raise ValueError("immutable history changed")
                previous, previous_hash = document, digest
            except (KeyError, TypeError, ValueError) as exc:
                raise AssessmentIntegrityConflict("Dynamic history integrity failed") from exc
        if previous is None:
            raise FileNotFoundError()
        return previous, previous_hash

    def _owned(self, identifier, actor):
        document, digest = self._load(identifier)
        if document.problem.created_by != actor:
            raise FileNotFoundError()
        return document, digest

    def _append(self, document, previous_hash):
        # model_copy is not validation; validate all additions at publication.
        document = DynamicDocument.model_validate(document.model_dump(exclude_unset=True))
        record = dict(previous_sha256=previous_hash, document=document.model_dump(mode="json", exclude_unset=True))
        record["sha256"] = canonical_sha256(record)
        path = self.folder(document.problem.problem_id) / f"revision_{document.revision:06d}.json"
        SubmissionStore._write_atomic_new(path, json.dumps(record, ensure_ascii=False, indent=2).encode())
        return self.project(document)

    @staticmethod
    def _event(kind, package, actor, timestamp, reason=None):
        return DynamicEvent(event_id="devt_" + uuid4().hex, event_type=kind,
            problem_id=package.problem_id, timestamp=timestamp, actor=actor,
            statement_version=package.statement_version, package_id=package.package_id,
            package_version=package.package_version, rubric_id=package.rubric_id,
            rubric_version=package.rubric_version, reason=reason)

    @staticmethod
    def _package(problem, statement, number, actor, timestamp, rubric=None, preparation=None):
        return DynamicProblemPackage(package_id="dpkg_" + uuid4().hex,
            problem_id=problem.problem_id, assessment_reference=problem.assessment_reference,
            package_version=number, statement_version=statement.version_number,
            statement_sha256=model_sha256(statement), rubric_id=rubric.rubric_id if rubric else None,
            rubric_version=rubric.version_number if rubric else None,
            rubric_sha256=model_sha256(rubric) if rubric else None,
            created_at=timestamp, created_by=actor, provenance=provenance(actor),
            **(dict(preparation_reference=PreparationReference(preparation_id=preparation.preparation_id,
                preparation_version=preparation.preparation_version, preparation_sha256=model_sha256(preparation)),
                preparation_status=preparation.status) if preparation else {}))

    @staticmethod
    def latest_preparation(document):
        rows = [p for p in document.preparations if p.statement_version == len(document.statements)]
        if not rows: return None
        latest_id = max(rows, key=lambda p:p.preparation_version).preparation_id
        return next(p for p in reversed(rows) if p.preparation_id == latest_id)

    @staticmethod
    def rubric_warnings(document, rubric):
        warnings = list(rubric.generation.warnings) if rubric.generation else []
        if rubric.preparation_reference:
            prep = next(p for p in reversed(document.preparations) if p.preparation_id == rubric.preparation_reference.preparation_id)
            warnings.extend(prep.analysis.warnings)
        return warnings

    @staticmethod
    def _expected(document, request):
        if request.expected_revision != document.revision:
            raise DynamicConflict("O problema mudou. Recarregue antes de salvar ou aprovar.")

    def create(self, request, actor, assessment_reference=None):
        with self._locked():
            timestamp = now()
            problem = DynamicProblem(problem_id="dyn_" + uuid4().hex, created_at=timestamp,
                created_by=actor, assessment_reference=assessment_reference)
            statement = StatementVersion(problem_id=problem.problem_id, version_number=1,
                title=request.title, statement=request.statement, max_score=request.max_score,
                created_at=timestamp, created_by=actor, provenance=provenance(actor))
            package = self._package(problem, statement, 1, actor, timestamp)
            document = DynamicDocument(revision=1, problem=problem, statements=(statement,), packages=(package,),
                events=tuple(self._event(kind, package, actor, timestamp) for kind in
                    ("dynamic_problem_created", "problem_statement_version_created")))
            return self._append(document, None)

    def get(self, identifier, actor):
        with self._locked():
            return self.project(self._owned(identifier, actor)[0])

    def list(self, actor):
        with self._locked():
            result = []
            for path in sorted(self.root.glob("dyn_*")):
                document, _ = self._load(path.name)
                if document.problem.created_by == actor:
                    result.append(self.project(document))
            return result

    def statement(self, identifier, request, actor):
        with self._locked():
            document, digest = self._owned(identifier, actor)
            self._expected(document, request)
            timestamp = now()
            statement = StatementVersion(problem_id=identifier, version_number=len(document.statements) + 1,
                title=request.title, statement=request.statement, max_score=request.max_score,
                created_at=timestamp, created_by=actor, provenance=provenance(actor))
            package = self._package(document.problem, statement, len(document.packages) + 1, actor, timestamp)
            events = list(document.events)
            if document.current_package_id:
                current = next(p for p in document.packages if p.package_id == document.current_package_id)
                events.append(self._event("rubric_superseded", current, actor, timestamp, "STATEMENT_CHANGED"))
            old_prep = self.latest_preparation(document)
            if old_prep:
                events.append(self._event("preparation_superseded", package, actor, timestamp, old_prep.preparation_id))
            events.append(self._event("problem_statement_version_created", package, actor, timestamp))
            return self._append(document.model_copy(update=dict(revision=document.revision + 1,
                statements=(*document.statements, statement), packages=(*document.packages, package),
                events=tuple(events), current_package_id=None)), digest)

    def save_rubric(self, identifier, request, actor, base_id=None, generation=None):
        from confia_lean_auditor.semantic_policy.service import dynamic_policy, DYNAMIC_VERSION
        if not generation and dynamic_policy() == DYNAMIC_VERSION:
            with self._locked():
                doc, _ = self._owned(identifier, actor)
                self._expected(doc, request)
                prep = self.latest_preparation(doc)
            if not prep or prep.status == 'FAILED':
                from .preparation import PreparationService
                from .semantic import TeacherPreparationProvider
                from .models import PreparationRequest
                data = PreparationService(self, TeacherPreparationProvider()).start(identifier,
                    PreparationRequest(expected_revision=request.expected_revision), actor)
                request = request.model_copy(update={'expected_revision':data['revision']})
        with self._locked():
            document, digest = self._owned(identifier, actor)
            self._expected(document, request)
            statement = document.statements[-1]
            if request.statement_version != statement.version_number or request.max_score != statement.max_score:
                raise DynamicConflict("A rubrica deve corresponder ao enunciado e total atuais.")
            prior = [r for r in document.rubrics if r.statement_version == statement.version_number]
            base = next((r for r in prior if r.rubric_id == base_id), None) if base_id else None
            if base_id and (base is None or base != prior[-1]):
                raise DynamicConflict("Edite somente a última rubrica deste enunciado.")
            if not base_id and prior:
                raise DynamicConflict("Já existe rubrica: edite a última versão.")
            preparation = self.latest_preparation(document)
            if generation:
                if not preparation or preparation.preparation_id != generation.preparation.preparation_id or preparation.status not in {'READY_FOR_REVIEW', 'REVIEW_REQUIRED'}:
                    raise DynamicConflict('A preparação mudou. Gere nova sugestão para a versão atual.')
                preparation_reference = generation.preparation
            elif base and base.preparation_reference and not request.replace_with_teacher:
                preparation_reference = base.preparation_reference
                preparation = next(p for p in reversed(document.preparations) if p.preparation_id == preparation_reference.preparation_id)
            elif preparation and preparation.status in {'READY_FOR_REVIEW', 'REVIEW_REQUIRED'}:
                preparation_reference = PreparationReference(preparation_id=preparation.preparation_id,
                    preparation_version=preparation.preparation_version, preparation_sha256=model_sha256(preparation))
            else:
                preparation, preparation_reference = None, None
            timestamp = now()
            rubric = RubricVersion(rubric_id="drub_" + uuid4().hex, problem_id=identifier,
                statement_version=statement.version_number, statement_sha256=model_sha256(statement),
                version_number=len(document.rubrics) + 1, draft_status="DRAFT_AI" if generation else "TEACHER_EDITED" if base else "DRAFT_TEACHER",
                supersedes_id=base.rubric_id if base else None, max_score=request.max_score, criteria=request.criteria,
                created_at=timestamp, created_by=actor,
                provenance=Provenance(origin='AI', model_provenance=generation.generation.model_dump(mode='json', exclude={'raw_output'})) if generation else provenance(actor),
                **(dict(preparation_reference=preparation_reference) if preparation_reference else {}),
                **(dict(generation=generation or base.generation) if generation or base and base.generation and not request.replace_with_teacher else {}))
            package = self._package(document.problem, statement, len(document.packages) + 1, actor, timestamp, rubric, preparation)
            event = self._event("rubric_edited" if base else "rubric_draft_created", package, actor, timestamp)
            return self._append(document.model_copy(update=dict(revision=document.revision + 1,
                rubrics=(*document.rubrics, rubric), packages=(*document.packages, package),
                events=(*document.events, event))), digest)

    def approve(self, identifier, rubric_id, request, actor):
        with self._locked():
            document, digest = self._owned(identifier, actor)
            self._expected(document, request)
            package = document.packages[-1]
            if package.rubric_id != rubric_id or package.statement_version != len(document.statements):
                raise DynamicConflict("Aprove somente a última rubrica do enunciado atual.")
            rubric = next(r for r in document.rubrics if r.rubric_id == rubric_id)
            if not rubric.criteria:
                raise DynamicConflict("Uma rubrica vazia não pode ser aprovada.")
            if any(a.rubric_id == rubric_id for a in document.approvals):
                raise DynamicConflict("Esta rubrica já foi aprovada.")
            latest = self.latest_preparation(document)
            if rubric.preparation_reference and (not latest or latest.preparation_id != rubric.preparation_reference.preparation_id):
                raise DynamicConflict('A rubrica usa uma preparação anterior. Gere uma nova sugestão ou forneça nova rubrica.')
            from confia_lean_auditor.semantic_policy.service import dynamic_policy, DYNAMIC_VERSION
            teacher_context = latest and latest.provenance and latest.provenance.provider == 'local_teacher_context'
            needs_review = any(w.requires_review for w in self.rubric_warnings(document, rubric))
            if teacher_context and dynamic_policy() == DYNAMIC_VERSION:
                needs_review = False  # approving their rubric is the explicit teacher action

            if needs_review and not getattr(request, 'acknowledge_warnings', False):
                raise DynamicConflict('Revise e reconheça explicitamente os avisos antes de aprovar.')
            timestamp = now()
            approval = Approval(package_id=package.package_id, rubric_id=rubric_id,
                approved_at=timestamp, approved_by=actor, package_sha256=model_sha256(package),
                rubric_sha256=model_sha256(rubric),
                **(dict(acknowledged_warnings=True) if needs_review else {}))
            events = list(document.events)
            if document.current_package_id:
                old = next(p for p in document.packages if p.package_id == document.current_package_id)
                events.append(self._event("rubric_superseded", old, actor, timestamp, "RUBRIC_REPLACED"))
            events.extend(self._event(kind, package, actor, timestamp) for kind in
                          ("rubric_approved", "dynamic_problem_package_activated"))
            return self._append(document.model_copy(update=dict(revision=document.revision + 1,
                approvals=(*document.approvals, approval), events=tuple(events),
                current_package_id=package.package_id)), digest)

    @staticmethod
    def project(document):
        data = document.model_dump(mode="json")
        approvals = {a.rubric_id: a for a in document.approvals}
        active = next((p for p in document.packages if p.package_id == document.current_package_id), None)
        for rubric in data["rubrics"]:
            approval = approvals.get(rubric["rubric_id"])
            rubric.update(status=("APPROVED" if active and active.rubric_id == rubric["rubric_id"] else "SUPERSEDED")
                if approval else rubric["draft_status"], is_current=bool(active and active.rubric_id == rubric["rubric_id"]),
                approved_at=approval.approved_at.isoformat() if approval else None,
                approved_by=approval.approved_by.model_dump() if approval else None)
        approved_packages = {a.package_id: a for a in document.approvals}
        for package in data["packages"]:
            package.update(status="APPROVED" if package["package_id"] in approved_packages else "DRAFT",
                is_current=package["package_id"] == document.current_package_id)
        preparations = {}
        for prep in document.preparations:
            preparations[prep.preparation_id] = prep
        latest = DynamicStore.latest_preparation(document)
        data['preparation_history'] = []
        for prep in preparations.values():
            row = prep.model_dump(mode='json')
            row['is_current'] = bool(latest and prep.preparation_id == latest.preparation_id)
            row['effective_status'] = prep.status if row['is_current'] else 'SUPERSEDED'
            data['preparation_history'].append(row)
        data['current_preparation'] = next((p for p in data['preparation_history'] if p['is_current']), None)
        for rubric, source in zip(data['rubrics'], document.rubrics):
            rubric['review_warnings'] = [w.model_dump(mode='json') for w in DynamicStore.rubric_warnings(document, source)]
        configuration = None
        if active:
            configuration = CorrectionConfiguration(mode="DYNAMIC", package=PackageReference(
                **{key: getattr(active, key) for key in PackageReference.model_fields if key != "package_sha256"},
                package_sha256=model_sha256(active))).model_dump(mode="json")
        return dict(**data, current_configuration=configuration,
            automatic_suggestion_available=provider_available(), correction_available=bool(active and latest and active.preparation_reference and active.preparation_reference.preparation_id==latest.preparation_id and latest.status in {"READY_FOR_REVIEW","REVIEW_REQUIRED"} and document.rubrics[-1].rubric_id==active.rubric_id),
            actor_notice="Identidade técnica de demonstração; não representa uma pessoa." if document.problem.created_by.kind == "TECHNICAL_DEMO" else None)
