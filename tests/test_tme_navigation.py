"""Metadata-only navigation, existing endpoint compatibility and bounded pages."""
from datetime import datetime, timezone, timedelta
import json

import pytest

from confia_lean_auditor.tme.home_summary import OperationalIndex, case_entry
from confia_lean_auditor.tme.models import CorrectionCase
from test_tme_pilot import setup, create_case
from test_tme_home_summary import home


def seed(count=123):
    now = datetime.now(timezone.utc)
    entries = {}
    for i in range(count):
        c = CorrectionCase(case_id=f'case_{i:032x}', created_by_user_id='tme-demo-evaluator',
            created_at=now - timedelta(seconds=i), external_candidate_ref=f'EXAM-{i // 5:05}',
            problem_id=f'ITA2025F2Q{i % 5 + 1}', source_mode='IMAGE_SCAN')
        entry = case_entry(c)
        entry['decided'] = i % 4 == 0
        if i % 4 == 1:
            entry['submission_id'] = 'sub_' + 'b' * 32
            entry['audit'] = dict(inconclusive=True, score=None, max_score=10)
        if i % 4 == 2:
            entry['submission_id'] = 'sub_' + 'b' * 32
            entry['audit'] = dict(inconclusive=False, score=0, max_score=10)
        entries[c.case_id] = entry
    other = dict(entries['case_' + '0' * 32], case_id='case_' + 'f' * 32, owner='other-owner', exam_code='PRIVATE')
    entries[other['case_id']] = other
    index = OperationalIndex()
    with index.locked():
        index.write(dict(version=1, generation=1, complete=True, cases=entries))
    return index


def test_queue_pagination_filters_metadata_and_owner(home):
    client, _, _ = home
    seed()
    first = client.get('/tme/cases?view=queue').json()
    second = client.get('/tme/cases?view=queue&page=2').json()
    last = client.get('/tme/cases?view=queue&page=3').json()
    assert [len(p['items']) for p in (first, second, last)] == [50, 50, 23]
    assert len({c['case_id'] for p in (first, second, last) for c in p['items']}) == 123
    assert first['total'] == 123
    assert 'PRIVATE' not in json.dumps(first)
    assert set(first['items'][0]) == {'case_id', 'exam_code', 'problem_id', 'source_mode',
        'operational_status', 'updated_at', 'suggested_score', 'max_score', 'suggestion_available'}
    filtered = client.get('/tme/cases', params=dict(view='queue',search='EXAM-00000',question='ITA2025F2Q2',status='inconclusive',source='IMAGE_SCAN')).json()
    assert filtered['total'] == 1
    assert filtered['items'][0]['suggested_score'] is None
    zero = client.get('/tme/cases?view=queue&question=ITA2025F2Q3').json()['items'][0]
    assert zero['suggested_score'] == 0 and zero['suggestion_available']
    assert client.get('/tme/cases?view=queue&page=999').json()['page'] == 3


def test_results_and_progress_match_home_known_questions(home):
    client, _, _ = home
    seed(13)
    summary = client.get('/tme/home-summary?period=all').json()
    results = client.get('/tme/cases?view=results').json()
    assert results['summary']['counts'] == summary['counts']
    assert sum(q['finalized'] for q in results['questions']) == summary['counts']['finalized']
    progress = client.get('/tme/cases?view=exams').json()
    assert sorted(e['known_items'] for e in progress['items']) == [3, 5, 5]
    for group in summary['exam_progress']:
        actual = next(e for e in progress['items'] if e['exam_code'] == group['exam_code'])
        assert actual['known_items'] == group['known_items']
        assert actual['completed_items'] == group['completed_items']
    assert all('case_id' in q for e in progress['items'] for q in e['questions'])


def test_exam_details_choose_latest_case_per_known_question(home):
    client, _, _ = home
    first = create_case(client, 'IMAGE_SCAN')
    second = create_case(client, 'IMAGE_SCAN')
    progress = client.get('/tme/cases?view=exams').json()['items']
    assert progress[0]['known_items'] == 1
    assert progress[0]['questions'][0]['case_id'] == second['case_id']
    details = client.get('/tme/cases?view=queue&exam=TME-0001').json()
    assert details['total'] == 1 and details['items'][0]['case_id'] == second['case_id']
    legacy = client.get('/tme/cases').json()
    assert {c['case_id'] for c in legacy} == {first['case_id'], second['case_id']}


def test_25000_cases_use_index_only_and_bound_payload(home, monkeypatch):
    client, _, _ = home
    index = seed(25000)
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.submissions.router import store
    def forbidden(*args, **kwargs):
        raise AssertionError('navigation must not load artifacts')
    monkeypatch.setattr(type(service()), 'list', forbidden)
    monkeypatch.setattr(type(store()), 'get_record', forbidden)
    monkeypatch.setattr(type(store()), 'list_transcriptions', forbidden)
    for view in ('queue', 'exams', 'results'):
        response = client.get('/tme/cases', params={'view':view})
        assert response.status_code == 200, response.text
        assert response.headers['cache-control'] == 'no-store'
        assert len(response.content) < 150000
        if view != 'results':
            assert len(response.json()['items']) == 50


def test_navigation_validation_and_unavailable_projection(home, monkeypatch):
    client, _, _ = home
    for query in ('view=wrong','view=queue&size=101','view=queue&page=0','view=queue&status=invalid'):
        assert client.get('/tme/cases?' + query).status_code == 422
    index = seed(1)
    index.dirty.touch()
    assert client.get('/tme/cases?view=queue').status_code == 503
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','0')
    assert client.get('/tme/cases?view=queue').status_code == 401
