"""Accepted transcription adapter; no mathematical inference or scoring rules."""
import hashlib
import json
import re
from pathlib import Path

from confia_lean_auditor.rubric.pauta import load_pauta
from confia_lean_auditor.rubric.pauta.engine import _fingerprint as config_digest
from confia_lean_auditor.submissions.integrity import model_sha256
from confia_lean_auditor.submission_audits.errors import AuditConflict, SourceIntegrityError
from .audit_models import PUBLIC_PROBLEMS, TMEAuditContext, TMEAuditResult
from .registry import TME_PROBLEMS, ROOT, audit_tme


class InvalidTMEProblem(AuditConflict):
    code = 'TME_PROBLEM_NOT_SUPPORTED'
    message = 'Identifique uma questão TME suportada antes da análise.'


def pauta_for(problem_id):
    if problem_id not in PUBLIC_PROBLEMS:
        raise InvalidTMEProblem()
    return load_pauta(ROOT / 'examples/pautas' / TME_PROBLEMS[PUBLIC_PROBLEMS[problem_id]])


def audit_context(problem_id, use_lean):
    config = pauta_for(problem_id)
    # Include all shared producers/checkers and the adapter itself; changes cause
    # a new identity. Read old runs with THEIR persisted version, never today's.
    app = ROOT / 'app/confia_lean_auditor'
    paths = set()
    for directory in ('tme', 'claims', 'student_claims', 'lean', 'core/math_canonical', 'rubric/pauta', 'submission_audits'):
        paths.update((app / directory).rglob('*.py'))
    paths.update(p for p in (ROOT / 'lean-toolchain', ROOT / 'lake-manifest.json', ROOT / 'pyproject.toml') if p.is_file())
    version = hashlib.sha256()
    for path in sorted(paths):
        version.update(str(path.relative_to(ROOT)).encode()); version.update(path.read_bytes())
    return TMEAuditContext(auditor_version='tme-integration.v1:' + version.hexdigest(),
        pauta_version=config.schema_version, pauta_sha256=config_digest(config), use_lean=use_lean)


def split_accepted_items(source):
    """Only explicit item metadata or standalone headers, never solution inference."""
    items, diagrams, warnings, locations = {}, {}, [], []
    current = None
    allowed_items = {item.id for item in pauta_for(source.problem_id).items}
    for segment in sorted(source.provenance.revision.segments, key=lambda s: (s.page_index, s.order)):
        if segment.tme_item_id is not None:
            if segment.tme_item_id not in allowed_items:
                raise SourceIntegrityError()
            current = segment.tme_item_id
        if segment.tme_diagrams:
            if source.problem_id != 'TME2026P2' or current is None:
                raise SourceIntegrityError()
            for diagram in segment.tme_diagrams:
                if not diagram.source.confirmed or diagram.source.origin != 'student':
                    raise SourceIntegrityError()
                if diagram.source.page_index not in (None, segment.page_index):
                    raise SourceIntegrityError()
            diagrams.setdefault(current, []).extend(d.model_dump(mode='json') for d in segment.tme_diagrams)
        if segment.kind == 'diagram':
            if not segment.tme_diagrams:
                warnings.append('Desenho sem representação confirmada; revisar as etapas dependentes dele.')
            continue
        if segment.kind == 'unknown':
            warnings.append('Trecho não identificado; não foi atribuído a um item automaticamente.')
            continue
        for value in (segment.text, segment.latex):
            if value is None:
                continue
            for line in (value if value.endswith("\n") else value + "\n").splitlines(keepends=True):
                marker = re.fullmatch(r'\s*(?:\[([abcd])\]|\(([abcd])\)|([abcd])\)|Item\s+\(([abcd])\))\s*', line, re.IGNORECASE)
                if marker:
                    label = next(v for v in marker.groups() if v).lower()
                    if segment.tme_item_id and label != segment.tme_item_id:
                        raise SourceIntegrityError()
                    if label not in allowed_items:
                        raise SourceIntegrityError()
                    current = label
                    continue
                if current is None:
                    if line.strip():
                        warnings.append('Trecho sem identificação de item; indique [a], [b] [c] ou [d], conforme a questão, na revisão aceita.')
                    continue
                items.setdefault(current, []).append(line)
                locations.append(dict(item=current, segment_id=segment.segment_id, page_index=segment.page_index))
    texts = {key: ''.join(lines).rstrip('\n') for key, lines in items.items()}
    # Preserve boundaries between segments; source revision remains the exact original.
    solution = dict(texts)
    for item, entries in diagrams.items():
        solution[item] = dict(text=texts.get(item, ''), diagrams=entries)
    return solution, list(dict.fromkeys(warnings)), locations


def audit_accepted_tme_transcription(source, output_dir):
    """Called only after AuditService validates the immutable acceptance receipt."""
    config = pauta_for(source.problem_id)
    if source.tme_context is None or source.provenance.acceptance.accepted_revision_sha256 != model_sha256(source.provenance.revision):
        raise SourceIntegrityError()
    solution, warnings, locations = split_accepted_items(source)
    # Stable content identity makes identical accepted mathematics independent of
    # input mode, case ID, acceptance timestamp and source revision identifiers.
    solution_id = 'accepted-' + hashlib.sha256(json.dumps(solution, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    bridge, assessment = audit_tme(source.problem_id, solution, solution_id=solution_id,
        use_lean=source.tme_context.use_lean)
    if any(path.is_symlink() for path in (output_dir, *output_dir.parents)):
        raise SourceIntegrityError()
    output_dir.mkdir(parents=True, exist_ok=False)
    result = TMEAuditResult(problem_id=source.problem_id,
        accepted_transcription_revision_id=f'{source.transcription_id}:{source.revision_number}',
        accepted_revision_sha256=source.provenance.acceptance.accepted_revision_sha256,
        context=source.tme_context, artifact_dir=str(output_dir), pauta=config,
        bridge=bridge, assessment=assessment, input_warnings=warnings)
    from .audit_artifacts import preserve_certificates
    preserve_certificates(result)
    (output_dir / 'audit.json').write_text(result.model_dump_json(indent=2))
    (output_dir / 'solution.txt').write_text(source.solution_text)
    (output_dir / 'accepted_revision.json').write_text(source.provenance.revision.model_dump_json(indent=2))
    (output_dir / 'input_mapping.json').write_text(json.dumps(dict(solution=solution, segment_mapping=locations), ensure_ascii=False, indent=2))
    return result
