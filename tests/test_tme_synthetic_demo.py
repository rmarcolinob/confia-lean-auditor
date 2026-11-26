"""Synthetic lifecycle against real stores and the existing accepted auditor."""
import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('synthetic_seed', ROOT / 'scripts/evaluation/seed_tme_synthetic_demo.py')
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    for name in ('SUBMISSIONS', 'SUBMISSION_AUDITS', 'TME_CASES', 'AUTH', 'INSTITUTIONAL'):
        monkeypatch.setenv(f'CONFIA_{name}_DIR', str(tmp_path / name.lower()))
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH', '1')
    monkeypatch.setenv('CONFIA_ENV', 'test')
    monkeypatch.setenv('CONFIA_AUTH_ENABLED', '1')
    user = seed.TMEEvaluator(seed.DEMO_EVALUATOR_ID)
    return user, tmp_path


@pytest.fixture
def rows():
    # CI has no private local dataset. A complete contract fixture remains valid.
    return [dict(solution_id=f'TME2026P{n}_{i:02}', problem_id=f'TME2026P{n}',
                 solution_text='(a)\n731 - 137 = 594' if n == 1 else 'Não sei resolver.',
                 synthetic_expected_score=19, max_score=20) for n in range(1, 6) for i in range(1, 26)]


def dataset_file(tmp_path, rows):
    p = tmp_path / 'dataset.jsonl'
    p.write_text('\n'.join(json.dumps(r) for r in rows))
    return p


def test_loader_count_distribution_and_local_dataset(tmp_path, rows):
    loaded = seed.load_dataset(dataset_file(tmp_path, rows))
    assert loaded == rows and len(loaded) == 125
    assert seed.Counter(r['problem_id'] for r in loaded) == {f'TME2026P{n}': 25 for n in range(1, 6)}
    if seed.DATASET.exists():
        local = seed.load_dataset()
        assert len(local) == 125
        for row in local:
            assert seed.convert_segments(seed.explicit_segments(row['solution_text']))[0] == row['solution_text']


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'wrong_problem', 'empty', 'score', 'bool_score'])
def test_loader_rejects_bad_dataset(tmp_path, rows, change):
    if change == 'missing': rows.pop()
    elif change == 'duplicate': rows[-1] = rows[0]
    elif change == 'wrong_problem': rows[-1]['problem_id'] = 'TME2026P1'
    elif change == 'empty': rows[-1]['solution_text'] = ' '
    elif change == 'score': rows[-1]['synthetic_expected_score'] = 21
    else: rows[-1]['synthetic_expected_score'] = True
    with pytest.raises(ValueError):
        seed.load_dataset(dataset_file(tmp_path, rows))


def test_seed_125_twice_and_workspace_filters(isolated, rows):
    user, _ = isolated
    first = seed.seed(rows, user)
    second = seed.seed(rows, user)
    assert first == second and len(first) == 125
    cases = seed.case_store().list_for_user(user)
    assert len(cases) == 125 and all(c.data_origin == 'synthetic_demo' and c.demo_seed == seed.SEED for c in cases)
    from confia_lean_auditor.tme.models import CaseCreate
    real = seed.case_store().create(CaseCreate(problem_id='TME2026P1', external_candidate_ref='REAL', source_mode='DIGITAL_INK'), user)
    from confia_lean_auditor.main import app
    with TestClient(app) as client:
        response = client.get('/tme/cases?view=queue&origin=synthetic_demo&size=100')
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['total'] == 125 and len(data['items']) == 100
        assert all(c['data_origin'] == 'synthetic_demo' for c in data['items'])
        assert client.get('/tme/cases?view=queue&origin=real').json()['items'][0]['case_id'] == real.case_id
        assert client.get('/tme/cases?view=queue&origin=synthetic_demo&question=TME2026P2').json()['total'] == 25
        entry = first[0]
        assert client.get(f"/tme/cases/{entry['case_id']}").json()['solution_id'] == rows[0]['solution_id']
        history = client.get(f"/tme/cases/{entry['case_id']}/transcriptions/{entry['transcription_id']}").json()
        assert history['revisions'][0]['status'] == 'ACCEPTED'
        assert history['acceptances'][0]['mathematical_validity_assessed'] is False


def test_real_audit_is_label_blind_accepted_and_persisted(isolated, rows, monkeypatch, tmp_path):
    user, _ = isolated
    entry = seed.seed(rows[:1], user)[0]
    from confia_lean_auditor.tme import accepted_audit
    original = accepted_audit.audit_tme
    observed = []
    def spy(problem_id, solution, **kwargs):
        assert problem_id == rows[0]['problem_id']
        assert set(kwargs) == {'solution_id', 'use_lean'}
        assert 'synthetic_expected_score' not in json.dumps(solution)
        observed.append((solution, kwargs))
        return original(problem_id, solution, **kwargs)
    monkeypatch.setattr(accepted_audit, 'audit_tme', spy)
    factory = seed.audit_service
    def no_lean_service():
        service = factory()
        service.tme_use_lean = False
        return service
    monkeypatch.setattr(seed, 'audit_service', no_lean_service)
    first = seed.audit([entry], tmp_path)
    second = seed.audit([entry], tmp_path)
    assert first == second and len(observed) == 1
    assert first[0]['status'] == 'COMPLETED'
    run = no_lean_service().get(first[0]['audit_run_id'])
    assert run.source.solution_text == rows[0]['solution_text']
    assert 'synthetic_expected_score' not in run.model_dump_json()
    assert run.result.assessment and run.result.bridge.auditor.facts
    assert not any(s.tme_diagrams for s in run.source.provenance.revision.segments)
    metadata_path = seed.case_store().folder(entry['case_id']) / 'demo-metadata.json'
    metadata = json.loads(metadata_path.read_text())
    metadata['synthetic_expected_score'] = 0
    seed.write_json(metadata_path, metadata)
    assert seed.audit([entry], tmp_path) == first  # label change cannot change audit identity/result


def test_clean_demo_preserves_real_submission_and_other_owners(isolated, rows, tmp_path, monkeypatch):
    user, _ = isolated
    from confia_lean_auditor.tme.models import CaseCreate
    from test_submissions import payload
    real = seed.case_store().create(CaseCreate(problem_id='ITA2025F2Q1', external_candidate_ref='REAL', source_mode='DIGITAL_INK'), user)
    receipt, _ = seed.submission_store().receive(seed.SubmissionRequest(**payload()), owner=user, tme_case_id=real.case_id)
    seed.case_store().bind(real.case_id, receipt.submission_id, user)
    entry = seed.seed(rows[:1], user)[0]
    other = seed.seed(rows[1:2], seed.TMEEvaluator('other-owner'))[0]
    service = seed.audit_service(); service.tme_use_lean = False
    run = service.execute(entry['submission_id'], seed.AuditRequest(**{k:entry[k] for k in ('transcription_id','revision_number','acceptance_id')}))
    root = seed.submission_store()._folder(receipt.submission_id)
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert seed.clean_demo(user) == 1
    assert not seed.case_store().root.joinpath(entry['case_id']).exists()
    assert not service._path(run.audit_run_id).exists()
    assert not Path(run.artifact_dir).exists()
    assert seed.case_store().read(other['case_id']).created_by_user_id == 'other-owner'
    assert {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()} == before
    assert seed.case_store().read(real.case_id).data_origin == 'real'
    assert seed.clean_demo(user) == 0


def test_clean_fails_closed_on_foreign_submission(isolated, rows):
    user, _ = isolated
    first, second = seed.seed(rows[:2], user)
    path = seed.case_store().folder(first['case_id']) / 'case.json'
    raw = json.loads(path.read_text())
    raw['submission_id'] = second['submission_id']
    seed.write_json(path, raw)
    with pytest.raises(ValueError): seed.clean_demo(user)
    assert seed.case_store().read(second['case_id'])
    assert seed.submission_store().get_record(first['submission_id'])


def test_no_invented_items_or_diagrams_and_lossless_split():
    text = '(a) texto\n\n(b) mais texto\nItem c\nfigura omitida\n'
    segments = seed.explicit_segments(text)
    assert [s.tme_item_id for s in segments] == ['a', 'b', 'c']
    assert seed.convert_segments(segments)[0] == text
    assert not any(s.tme_diagrams for s in segments)
    assert seed.explicit_segments('1. texto\n2. outro')[0].tme_item_id is None


def test_metrics_null_is_not_zero_and_sample_shortfalls():
    rows = [dict(solution_id=str(i), score=0 if i else None, synthetic_expected_score=5,
        status='COMPLETED', needs_review=True, absolute_difference=5 if i else None,
        indeterminate_ratio=1, lean_checks=0) for i in range(30)]
    summary = seed.metrics(rows, 30)
    assert summary['scores_numeric'] == 29 and summary['score_null'] == 1
    assert summary['synthetic_mae'] == 5 and summary['mean_bias'] == -5
    sample = seed.sample_cases(rows)
    assert len(sample['cases']) == len({r['solution_id'] for r in sample['cases']}) == 25
    assert sample['quotas'][0]['selected'] == 0 and sample['quotas'][0]['shortfall'] == 5
