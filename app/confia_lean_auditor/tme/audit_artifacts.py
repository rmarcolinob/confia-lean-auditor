"""Durable copies of local certificates; the mathematical result is not rewritten."""
import hashlib
from pathlib import Path
from confia_lean_auditor.core.paths import get_repo_root


def formal_references(result):
    for fact in result.bridge.auditor.facts:
        check = fact.student_check
        if not check:
            continue
        status = check.get('formal_status') or check.get('status')
        if status == 'verified':
            if check.get('compiled') is not True:
                raise ValueError('Uncompiled formal evidence')
            path, kind = check.get('lean_file'), 'student_proof'
        elif status == 'refuted':
            if check.get('refutation_verified') is not True:
                raise ValueError('Unverified refutation')
            path, kind = check.get('refutation_lean_file'), 'refutation'
        else:
            continue
        if not path:
            raise ValueError('Missing formal certificate')
        filename = hashlib.sha256(path.encode()).hexdigest() + '.lean'
        yield kind, fact.fact_id + ':' + check['id'], path, str(Path(result.artifact_dir) / 'certificates' / filename)


def preserve_certificates(result):
    from confia_lean_auditor.submission_audits.artifacts import controlled_file
    for _, _, original, target in formal_references(result):
        source = controlled_file(get_repo_root() / 'artifacts/student_claim_checks', original)
        path = Path(target)
        path.parent.mkdir(exist_ok=True)
        if not path.exists():
            with path.open('xb') as handle:
                handle.write(source.read_bytes())


def required_references(result):
    root = Path(result.artifact_dir)
    refs = [('export', name, str(root / name)) for name in
            ('audit.json', 'solution.txt', 'accepted_revision.json', 'input_mapping.json')]
    refs.extend((kind, relation, target) for kind, relation, _, target in formal_references(result))
    return root, refs
