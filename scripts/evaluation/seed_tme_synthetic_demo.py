#!/usr/bin/env python3
"""Import accepted synthetic transcriptions into the real TME pilot, without OCR.

Evaluation labels live only in demo-metadata.json and evaluation exports. The
production AuditService receives only an acceptance reference. The frozen
accepted adapter keeps its own content-derived mathematical solution identity;
solution_id from the dataset remains the operational/evaluation identity.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import struct
import subprocess
import sys
import zlib
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
from confia_lean_auditor.capture.schemas import CaptureDocument
from confia_lean_auditor.submissions.schemas import SubmissionRequest, CreateTranscriptionRequest, AcceptTranscriptionRequest, TranscriptionSegment
from confia_lean_auditor.submissions.router import store as submission_store
from confia_lean_auditor.submission_audits.router import service as audit_service
from confia_lean_auditor.submission_audits.schemas import AuditRequest
from confia_lean_auditor.submission_audits.source import convert_segments
from confia_lean_auditor.tme.auth import TMEEvaluator, DEMO_EVALUATOR_ID
from confia_lean_auditor.tme.models import CorrectionCase
from confia_lean_auditor.tme.store import case_store
from confia_lean_auditor.tme.home_summary import project_case, rebuild_index, OperationalIndex, ConcurrentProjectionUpdate

SEED = 'seed_tme_synthetic_demo.v1'
ALTERNATIVE_PATHS = {'b.alternative', 'b.parallelogram_path', 'c.cases_path', 'c.general_integer_break_path'}
DATASET = ROOT / 'datasets/solucoes_tme2026/solucoes_tme2026.jsonl'
NOTICE = 'Os rótulos de referência são sintéticos e não substituem avaliação humana.'


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.pending')
    with temporary.open('w', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_dataset(path=DATASET):
    records = []
    for number, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or set(row) != {'solution_id', 'problem_id', 'solution_text', 'synthetic_expected_score', 'max_score'}:
            raise ValueError(f'Invalid dataset fields at line {number}')
        if not isinstance(row['solution_id'], str) or not re.fullmatch(r'[A-Za-z0-9._:-]{1,80}', row['solution_id']):
            raise ValueError(f'Invalid solution identity at line {number}')
        if not isinstance(row['solution_text'], str) or not row['solution_text'].strip():
            raise ValueError(f'Empty solution at line {number}')
        score = row['synthetic_expected_score']
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 20 or row['max_score'] != 20:
            raise ValueError(f'Invalid evaluation score at line {number}')
        records.append(row)
    if len(records) != 125 or len({r['solution_id'] for r in records}) != 125:
        raise ValueError('Expected exactly 125 unique solutions')
    if Counter(r['problem_id'] for r in records) != {f'TME2026P{n}': 25 for n in range(1, 6)}:
        raise ValueError('Expected exactly 25 solutions per problem P1–P5')
    return records


def case_id_for(solution_id):
    return 'case_' + digest(SEED + ':synthetic_demo:' + solution_id)[:32]


def explicit_segments(text):
    """Only label syntax, no inference from mathematics, numbering or labels.

    Keep all original characters, including item headers. Segment boundaries
    replace exactly one original newline, restored by convert_segments.
    """
    marker = re.compile(r'^[ \t]*(?:\(([a-d])\)|\[([a-d])\]|([a-d])\)|Item\s+\(?([a-d])\)?(?=\s|:|$))', re.I)
    chunks, current, lines = [], None, []
    for line in text.split('\n'):
        match = marker.match(line)
        if match:
            if lines:
                chunks.append((current, '\n'.join(lines)))
            current = next(g.lower() for g in match.groups() if g)
            lines = []
        lines.append(line)
    if lines:
        chunks.append((current, '\n'.join(lines)))
    segments = [TranscriptionSegment(segment_id=f'synthetic-text-{i}', page_index=0, order=i,
                 kind='text', text=value, **({'tme_item_id': item} if item else {}))
                for i, (item, value) in enumerate(chunks)]
    assert convert_segments(segments)[0] == text
    return segments


def blank_png():
    # Transport envelope required by the existing tablet contract, no drawing
    # and no mathematical evidence. The accepted transcription is the source.
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\0\xff\xff\xff\xff')) + chunk(b'IEND', b'')


@contextmanager
def demo_lock():
    root = case_store().root
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError('Invalid cases directory')
    fd = os.open(root / '.synthetic-demo.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a+b') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def assert_owned(case, row, user):
    if (case.case_id != case_id_for(row['solution_id']) or case.solution_id != row['solution_id']
            or case.problem_id != row['problem_id'] or case.data_origin != 'synthetic_demo'
            or case.demo_seed != SEED or case.created_by_user_id != user.user_id):
        raise ValueError('Refusing to touch a case not owned by this synthetic seed')


def seed_one(row, user):
    cases, submissions = case_store(), submission_store()
    cid = case_id_for(row['solution_id'])
    folder = cases.root / cid
    with cases.locked():
        if folder.exists():
            case = cases.read(cid)
            assert_owned(case, row, user)
        else:
            case = CorrectionCase(case_id=cid, problem_id=row['problem_id'], external_candidate_ref=row['solution_id'],
                source_mode='DIGITAL_INK', created_by_user_id=user.user_id, created_at=datetime.now(timezone.utc),
                data_origin='synthetic_demo', demo_seed=SEED, solution_id=row['solution_id'])
            folder.mkdir(mode=0o700)
            submissions._write_atomic_new(folder / 'case.json', case.model_dump_json(indent=2).encode())
    metadata = dict(seed=SEED, data_origin='synthetic_demo', case_id=cid, **row)
    metadata_path = folder / 'demo-metadata.json'
    if metadata_path.is_symlink():
        raise ValueError('Invalid demo metadata path')
    if metadata_path.exists() and json.loads(metadata_path.read_text()) != metadata:
        raise ValueError('Dataset changed; refusing to overwrite accepted demo data')
    write_json(metadata_path, metadata)
    snapshot_id = 'synthetic_demo:' + digest(SEED + ':' + row['solution_id'])
    snapshot = CaptureDocument(document_kind='local_snapshot', draft_id=snapshot_id, local_snapshot_id=snapshot_id,
        problem_id=row['problem_id'], pages=[dict(page_id='synthetic-empty-envelope', index=0, logical_width=1, logical_height=1)],
        client_created_at=case.created_at, client_updated_at=case.created_at)
    receipt, _ = submissions.receive(SubmissionRequest(snapshot_json=snapshot.model_dump_json(),
        pages=[dict(page_id='synthetic-empty-envelope', png_base64=base64.b64encode(blank_png()).decode())],
        student_reference='synthetic_demo:' + digest(row['solution_id'])[:32]), owner=user, tme_case_id=cid)
    case = cases.bind(cid, receipt.submission_id, user)
    existing = submissions.list_transcriptions(receipt.submission_id)
    segments = explicit_segments(row['solution_text'])
    if existing:
        if len(existing) != 1:
            raise ValueError('Demo transcription was manually modified; refusing to replace it')
        revision = existing[0].latest_revision
        if revision.revision_number != 1 or revision.segments != segments:
            raise ValueError('Demo transcription was manually modified; refusing to replace it')
    else:
        revision = submissions.create_transcription(receipt.submission_id, CreateTranscriptionRequest(
            reviewer_reference=SEED, segments=segments))
    accepted = submissions.accept_transcription(revision.transcription_id, AcceptTranscriptionRequest(
        revision_number=1, reviewer_reference=SEED,
        acceptance_note='synthetic_demo: texto importado fielmente; nenhuma validação humana ou matemática.'))
    return dict(solution_id=row['solution_id'], problem_id=row['problem_id'], case_id=cid,
        submission_id=receipt.submission_id, transcription_id=revision.transcription_id,
        revision_number=1, acceptance_id=accepted.acceptance.acceptance_id,
        data_origin='synthetic_demo', max_score=20, workspace_url=f'/tme?case_id={cid}')


def seed(records, user):
    with demo_lock():
        imported = [seed_one(row, user) for row in records]
        for attempt in range(3):
            try:
                rebuild_index()
                break
            except ConcurrentProjectionUpdate:
                if attempt == 2:
                    raise
    return imported


def imported_existing(records, user):
    imported = []
    for row in records:
        case = case_store().read(case_id_for(row['solution_id']))
        assert_owned(case, row, user)
        summaries = submission_store().list_transcriptions(case.submission_id)
        if len(summaries) != 1:
            raise ValueError('Expected one demo transcription')
        history = submission_store().transcription_history(summaries[0].transcription.transcription_id)
        if len(history.revisions) != 1 or len(history.acceptances) != 1 or convert_segments(history.revisions[0].segments)[0] != row['solution_text']:
            raise ValueError('Demo transcription changed')
        imported.append(dict(solution_id=row['solution_id'], problem_id=row['problem_id'], case_id=case.case_id,
            submission_id=case.submission_id, transcription_id=history.transcription.transcription_id,
            revision_number=1, acceptance_id=history.acceptances[0].acceptance_id,
            data_origin='synthetic_demo', max_score=20, workspace_url=f'/tme?case_id={case.case_id}'))
    return imported


def walk_decisions(items):
    for item in items:
        yield item
        yield from walk_decisions(item.children)


def result_row(entry, run):
    result = run.result
    out = dict(entry, audit_run_id=run.audit_run_id, status=run.status, error_code=run.error_code,
               score=result.score if result else None, needs_review=result.needs_review if result else None,
               indeterminate_count=0, indeterminate_ratio=None, lean_refutations=[], lean_checks=0,
               alternative_methods=[], carry_forward=[], input_warnings=[], technical_fact_errors=[], fact_count=0)
    if result:
        obligations = result.bridge.evidence.obligations
        uncertain = sum(o.status in ('indeterminate', 'technical_error') for o in obligations)
        decisions = list(walk_decisions(result.assessment.items))
        facts = result.bridge.auditor.facts
        out.update(fact_count=len(facts), technical_fact_errors=[dict(fact_id=f.fact_id, status=f.verification.status,
            failure_category=(f.student_check or {}).get('failure_category'),
            diagnostic=(f.student_check or {}).get('stdout', '')[-1500:])
            for f in facts if f.verification.status == 'technical_error'], indeterminate_count=uncertain, indeterminate_ratio=uncertain / len(obligations) if obligations else 0,
            lean_refutations=[f.fact_id for f in facts if f.verification_source == 'student_lean' and f.verification.status == 'refuted'],
            lean_checks=sum(f.verification_source == 'student_lean' for f in facts),
            alternative_methods=[dict(item_id=d.item_id, path=d.selected_method_path) for d in decisions if d.selected_method_path in ALTERNATIVE_PATHS and d.known_points > 0],
            carry_forward=[d.item_id for d in decisions if d.carry_forward_applied], input_warnings=result.input_warnings,
            item_scores=[dict(item_id=d.item_id, score=float(d.points_awarded) if d.points_awarded is not None else None,
                              max_score=float(d.max_points)) for d in result.assessment.items],
            artifact_dir=run.artifact_dir, result_sha256=run.result_sha256, auditor_version=run.auditor_version)
    return out


def audit(imported, output):
    # Evaluation scores are deliberately absent from both entry and request.
    results = []
    service = audit_service()
    with (output / 'audit_results.jsonl').open('w', encoding='utf-8') as stream:
        for index, entry in enumerate(imported, 1):
            try:
                run = service.execute(entry['submission_id'], AuditRequest(**{key: entry[key] for key in
                    ('transcription_id', 'revision_number', 'acceptance_id')}))
                result = result_row(entry, run)
            except Exception as error:
                result = dict(entry, status='EXCEPTION', error_code=type(error).__name__, score=None, needs_review=None)
            results.append(result)
            stream.write(json.dumps(result, ensure_ascii=False) + '\n')
            stream.flush()
            print(f"[{index}/{len(imported)}] {entry['solution_id']}: {result['status']} score={result['score']}", flush=True)
    return results


def metrics(rows, expected):
    numeric = [r for r in rows if r['score'] is not None]
    differences = [r['score'] - r['synthetic_expected_score'] for r in numeric]
    absolute = [abs(d) for d in differences]
    percent = lambda count: 100 * count / len(numeric) if numeric else None
    return dict(expected=expected, imported=len(rows), audited=sum(r['status'] == 'COMPLETED' for r in rows),
        exceptions=sum(r['status'] != 'COMPLETED' for r in rows), scores_numeric=len(numeric),
        score_null=sum(r['score'] is None for r in rows), needs_review=sum(bool(r.get('needs_review')) for r in rows),
        comparison='concordância com rótulo sintético', comparison_denominator=len(numeric),
        exact_count=absolute.count(0), exact_percent=percent(absolute.count(0)),
        synthetic_mae=statistics.mean(absolute) if absolute else None,
        median_absolute_difference=statistics.median(absolute) if absolute else None,
        within_1_percent=percent(sum(d <= 1 for d in absolute)), within_2_percent=percent(sum(d <= 2 for d in absolute)),
        mean_bias=statistics.mean(differences) if differences else None, max_absolute_difference=max(absolute, default=None),
        score_distribution=dict(sorted(Counter(str(r['score']) for r in rows).items())))


def sample_cases(rows):
    # 25 distinct cases. Short categories are recorded, never relabelled.
    selected, used, quotas = [], set(), []
    criteria = [
        ('concordância exata', lambda r: r['absolute_difference'] == 0),
        ('diferença 1', lambda r: r['absolute_difference'] == 1),
        ('diferença ≥ 2', lambda r: r['absolute_difference'] is not None and r['absolute_difference'] >= 2),
        ('alta indeterminação', lambda r: (r.get('indeterminate_ratio') or 0) >= .5),
        ('Lean / método / carry-forward', lambda r: bool(r.get('lean_checks') or r.get('alternative_methods') or r.get('carry_forward'))),
    ]
    candidates = {name: sorted((r for r in rows if predicate(r)),
        key=lambda r: (-(r.get('indeterminate_ratio') or 0), r['solution_id'])) for name, predicate in criteria}
    # Bipartite matching prevents an early category consuming the only Lean
    # examples when another assignment could meet all five requested quotas.
    owners = {}
    def assign(slot, seen):
        for row in candidates[slot[0]]:
            sid = row['solution_id']
            if sid in seen:
                continue
            seen.add(sid)
            if sid not in owners or assign(owners[sid], seen):
                owners[sid] = slot
                return True
        return False
    for name in sorted(candidates, key=lambda name: len(candidates[name])):
        for i in range(5):
            assign((name, i), set())
    for name, _ in criteria:
        picks = [r for r in candidates[name] if owners.get(r['solution_id'], (None,))[0] == name]
        quotas.append(dict(category=name, requested=5, eligible=len(candidates[name]), selected=len(picks), shortfall=5-len(picks)))
        for row in picks:
            used.add(row['solution_id'])
            selected.append(dict(row, sample_group=name))
    for row in sorted(rows, key=lambda r: (-(r.get('indeterminate_ratio') or 0), r['solution_id'])):
        if len(selected) >= 25:
            break
        if row['solution_id'] not in used:
            used.add(row['solution_id'])
            selected.append(dict(row, sample_group='complemento — categoria insuficiente'))
    return dict(requested=25, selected=len(selected), quotas=quotas, cases=selected)


def report(records, imported, results, output, freeze):
    # This join happens only after all audit executions have finished.
    labels = {r['solution_id']: r['synthetic_expected_score'] for r in records}
    rows = [dict(r, synthetic_expected_score=labels[r['solution_id']],
                 difference=r['score'] - labels[r['solution_id']] if r['score'] is not None else None,
                 absolute_difference=abs(r['score'] - labels[r['solution_id']]) if r['score'] is not None else None)
            for r in results]
    summary = metrics(rows, 125)
    summary.update(notice=NOTICE, engine_freeze=freeze, use_lean=True,
                   high_indeterminacy_definition='≥50% das obrigações indeterminadas ou com erro técnico',
                   large_difference_definition='diferença absoluta ≥3')
    by_problem = {f'TME2026P{n}': metrics([r for r in rows if r['problem_id'] == f'TME2026P{n}'], 25) for n in range(1, 6)}
    buckets = {str(n): [r for r in rows if r['absolute_difference'] == n] for n in range(3)}
    buckets['≥3'] = [r for r in rows if r['absolute_difference'] is not None and r['absolute_difference'] >= 3]
    buckets.update(below=[r for r in rows if r['difference'] is not None and r['difference'] <= -3],
        above=[r for r in rows if r['difference'] is not None and r['difference'] >= 3],
        score_null=[r for r in rows if r['score'] is None],
        high_indeterminacy=[r for r in rows if (r.get('indeterminate_ratio') or 0) >= .5],
        lean_refutations=[r for r in rows if r.get('lean_refutations')],
        alternative_methods=[r for r in rows if r.get('alternative_methods')],
        carry_forward=[r for r in rows if r.get('carry_forward')],
        technical_errors=[r for r in rows if r.get('technical_fact_errors')],
        input_mapping_warnings=[r for r in rows if r.get('input_warnings')],
        no_facts=[r for r in rows if r.get('fact_count') == 0])
    sample = sample_cases(rows)
    groups = {r['case_id']: [r['sample_group']] for r in sample['cases']}
    with demo_lock():
        cases = case_store()
        for entry in imported:
            case = cases.read(entry['case_id'])
            if case.demo_seed != SEED or case.data_origin != 'synthetic_demo':
                raise ValueError('Invalid demo case')
            case = case.model_copy(update={'demo_sample_groups': groups.get(case.case_id, [])})
            write_json(cases.folder(case.case_id) / 'case.json', case.model_dump(mode='json'))
            project_case(case, root=cases.root)
    for filename, value in [('summary.json', summary), ('summary_by_problem.json', by_problem),
                            ('score_disagreements.json', buckets), ('workspace_sample.json', sample)]:
        write_json(output / filename, value)
    lines = ['# Validação funcional sintética TME', '', NOTICE, '',
        f"Branch: `{freeze['branch']}`. SHA: `{freeze['sha']}`.",
        f"Status inicial: `{freeze.get('status_short') or 'limpo'}`. Motor protegido: hashes conferidos.", '',
        '## Fluxo e limites', '',
        'CorrectionCase → Submission → TranscriptionRevision aceita → AuditService → audit_tme → FactResult → PautaEvidence → PautaEngine → AuditRun.',
        'Lean habilitado. Sem OCR/Mathpix, sem notas mockadas, sem DiagramState inventado, sem decisão humana automática.',
        'O envelope digital contém uma página branca de 1×1, sem traços; não é evidência matemática. A fonte é o texto aceito, preservado integralmente.',
        'Somente rótulos explícitos (a), a), [a] e Item a recebem metadados de item. Não se inferem itens pela matemática ou por listas numeradas.',
        'solution_id é preservado no caso e na avaliação. O adaptador congelado mantém seu ID matemático derivado do conteúdo.',
        'synthetic_expected_score fica exclusivamente no metadado de avaliação; não entra na transcrição, no AuditSource ou na chamada ao auditor.', '',
        '## Concordância com rótulo sintético', '',
        'Percentuais e diferenças usam apenas notas numéricas; null não é convertido em zero. Diferença mediana = mediana absoluta.', '',
        '| Problema | Importados | Auditados | Numéricas | Null | Revisão | Exata % | MAE sintético | ±1 % | ±2 % | Viés |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name, data in [('Todos', summary), *by_problem.items()]:
        vals = [data[k] for k in ('imported', 'audited', 'scores_numeric', 'score_null', 'needs_review', 'exact_percent', 'synthetic_mae', 'within_1_percent', 'within_2_percent', 'mean_bias')]
        lines.append('| ' + name + ' | ' + ' | '.join(f'{v:.3f}' if isinstance(v, float) else str(v) for v in vals) + ' |')
    lines += ['', f"Exceções/falhas: {summary['exceptions']}. Mediana absoluta: {summary['median_absolute_difference']}. Maior diferença: {summary['max_absolute_difference']}.",
        '', 'Distribuição das notas ConfIA: `' + json.dumps(summary['score_distribution']) + '`.', '',
        '## Divergências e inspeção', '',
        'Distribuição das diferenças: ' + ', '.join(f'{k}: {len(buckets[k])}' for k in ('0', '1', '2', '≥3')) + '.',
        'Sinalizadores: ' + ', '.join(f'{k}: {len(buckets[k])}' for k in ('below', 'above', 'score_null', 'high_indeterminacy', 'lean_refutations', 'alternative_methods', 'carry_forward', 'technical_errors', 'input_mapping_warnings', 'no_facts')) + '.',
        'Alta indeterminação: ≥50% das obrigações indeterminadas/com erro técnico. Muito abaixo/acima: diferença ≥3 pontos. Métodos listados são caminhos selecionados pelo motor; não se infere método da nota.', '',
        'Maiores diferenças:', '']
    for row in sorted((r for r in rows if r['absolute_difference'] is not None), key=lambda r: -r['absolute_difference'])[:10]:
        lines.append(f"- [{row['solution_id']}]({row['workspace_url']}): ConfIA {row['score']}; sintético {row['synthetic_expected_score']}; diferença {row['difference']}.")
    if buckets['technical_errors']:
        lines += ['', 'Falhas técnicas preservadas (não são refutações matemáticas):', '']
        for row in buckets['technical_errors']:
            details = ', '.join(f"{e['fact_id']}: {e['failure_category']}" for e in row['technical_fact_errors'])
            lines.append(f"- {row['solution_id']}: {details}. Consulte o AuditRun para o diagnóstico Lean integral.")
    lines += ['', 'Amostra de 25 casos distintos. Categorias sem cinco casos elegíveis ficam explicitamente registradas; complementos não são apresentados como membros dessas categorias.', '']
    for q in sample['quotas']:
        lines.append(f"- {q['category']}: {q['selected']}/5 selecionados; {q['eligible']} elegíveis; déficit {q['shortfall']}.")
    lines += ['', '## Navegação e repetição', '',
        'Abrir `/tme?view=queue&origin=synthetic_demo`. Filtrar por questão ou buscar solution_id. A amostra está em `/tme?view=queue&origin=synthetic_demo&sample=selected`.',
        'Os casos pertencem ao avaliador informado ao CLI (por padrão tme-demo-evaluator). Para o piloto local, iniciar com CONFIA_TME_DEMO_NO_AUTH=1; não altera autenticação de produção.',
        'Abrir cada caso para transcrição aceita, nota e itens, critérios/evidências, verificação formal e indeterminações. A decisão humana permanece em separado.',
        '`python scripts/evaluation/seed_tme_synthetic_demo.py --seed --audit` reutiliza as identidades e os AuditRuns. `--clean-demo` remove apenas registros com identidade, origem, metadado e vínculos validados deste seed.',
        'Nenhuma divergência foi corrigida no motor; os resultados não estimam qualidade em produção.', '']
    (output / 'TME_SYNTHETIC_DEMO_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    return summary


def clean_demo(user):
    """Fail closed: validate the entire deletion plan before deleting anything."""
    with demo_lock():
        cases, submissions, service = case_store(), submission_store(), audit_service()
        all_cases = [cases.read(p.name) for p in cases.root.glob('case_*')]
        selected = [c for c in all_cases if c.demo_seed == SEED and c.data_origin == 'synthetic_demo' and c.created_by_user_id == user.user_id]
        plan = []
        for case in selected:
            folder = cases.folder(case.case_id)
            metadata_path = folder / 'demo-metadata.json'
            if metadata_path.is_symlink():
                raise ValueError('Invalid demo metadata')
            metadata = json.loads(metadata_path.read_text())
            assert_owned(case, metadata, user)
            if metadata.get('seed') != SEED or metadata.get('data_origin') != 'synthetic_demo' or metadata.get('case_id') != case.case_id:
                raise ValueError('Invalid demo metadata')
            paths = [folder]
            if case.submission_id:
                record = submissions.assert_submission_integrity(case.submission_id)
                if (record.tme_case_id != case.case_id or record.submitted_by_user_id != user.user_id
                        or record.problem_id != case.problem_id or record.snapshot_id != 'synthetic_demo:' + digest(SEED + ':' + case.solution_id)
                        or any(c.case_id != case.case_id and c.submission_id == case.submission_id for c in all_cases)):
                    raise ValueError('Refusing cleanup of a shared or non-demo submission')
                paths.insert(0, submissions._folder(case.submission_id))
                for path in service.root.glob('aud_*.json'):
                    raw = json.loads(path.read_text())
                    if raw.get('submission_id') != case.submission_id:
                        continue
                    run = service._read(path.stem)
                    paths.insert(0, path)
                    if run.artifact_dir:
                        artifact = Path(run.artifact_dir)
                        if artifact.parent.resolve() != (service.root / 'artifacts').resolve() or not artifact.name.startswith(run.audit_run_id + '-'):
                            raise ValueError('Refusing cleanup outside owned audit artifact directory')
                        paths.insert(0, artifact)
            for path in paths:
                if any(p.is_symlink() for p in (path, *path.parents)) or (path.is_dir() and any(p.is_symlink() for p in path.rglob('*'))):
                    raise ValueError('Refusing cleanup through symlinks')
            plan.append((case.case_id, paths))
        for cid, paths in plan:
            for path in paths:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            OperationalIndex(cases.root).update(lambda entries, cid=cid: entries.pop(cid, None))
        return len(plan)


def freeze_state():
    git = lambda *args: subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    prefixes = ('app/confia_lean_auditor/rubric/pauta/', 'app/confia_lean_auditor/student_claims/',
        'app/confia_lean_auditor/claims/', 'app/confia_lean_auditor/lean/', 'app/confia_lean_auditor/core/math_canonical/',
        'ConfiaLeanAuditor/', 'examples/pautas/')
    extra = {'lean-toolchain', 'lakefile.toml', 'lake-manifest.json', 'ConfiaLeanAuditor.lean'} | {
        'app/confia_lean_auditor/tme/' + name + '.py' for name in ('accepted_audit', 'registry', 'p2_diagram', 'p3_machine', 'p4_geometry', 'p5_integer_break')}
    files = [p for p in git('ls-files').splitlines() if p.startswith(prefixes) or p in extra]
    return dict(branch=git('branch', '--show-current'), sha=git('rev-parse', 'HEAD'), status_short=git('status', '--short'),
                files={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', action='store_true')
    parser.add_argument('--audit', action='store_true')
    parser.add_argument('--clean-demo', action='store_true')
    parser.add_argument('--dataset', type=Path, default=DATASET)
    parser.add_argument('--evaluator-id', default=DEMO_EVALUATOR_ID)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--freeze-manifest', type=Path)
    args = parser.parse_args()
    if not (args.seed or args.audit or args.clean_demo) or (args.clean_demo and (args.seed or args.audit)):
        parser.error('Use --seed and/or --audit, or --clean-demo alone')
    user = TMEEvaluator(args.evaluator_id)
    if args.clean_demo:
        print(json.dumps(dict(removed=clean_demo(user))))
        return
    frozen = json.loads(args.freeze_manifest.read_text()) if args.freeze_manifest else freeze_state()
    current = freeze_state()
    if frozen['sha'] != current['sha'] or any(current['files'].get(k) != v for k, v in frozen['files'].items()):
        raise ValueError('Frozen engine changed; refusing execution')
    timestamp = datetime.now(ZoneInfo('America/Fortaleza')).strftime('%Y%m%d_%H%M%S')
    output = args.output or ROOT / 'artifacts/evaluations' / ('tme_synthetic_demo_' + timestamp)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / 'engine_freeze.json', frozen)
    write_json(output / 'execution_worktree.json', current)
    records = load_dataset(args.dataset)
    write_json(output / 'dataset_manifest.json', dict(path=str(args.dataset.resolve()), sha256=hashlib.sha256(args.dataset.read_bytes()).hexdigest()))
    imported = seed(records, user) if args.seed else imported_existing(records, user)
    write_json(output / 'imported_cases.json', imported)
    if args.audit:
        with demo_lock():
            results = audit(imported, output)
        if freeze_state()['files'] != current['files']:
            raise ValueError('Protected engine changed during execution')
        summary = report(records, imported, results, output, frozen)
        print(json.dumps(summary, ensure_ascii=False, default=str))
    print(f'Artifacts: {output}', flush=True)


if __name__ == '__main__':
    main()
