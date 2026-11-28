"""Real institutional stores/HTTP; synthetic text and explicit simulated LLMs."""
import json
import pytest
from test_core_auth import auth_case
from test_dynamic_school import school, text_attempt, finish


def metrics(school, path='/management/overview'):
    response = school['clients']('manager.a').get(path)
    assert response.status_code == 200, response.text
    return response.json()['metrics']


def completed(school):
    attempt = text_attempt(school)
    response = school['student'].post('/dynamic/student/attempts/' + attempt['attempt_id'] + '/submit')
    assert response.status_code == 200, response.text
    return attempt, finish(school, attempt)


def test_manager_counts_current_question_decisions_and_explicit_release(school):
    attempt, final = completed(school)
    before = metrics(school)
    assert before['submissions_count'] == 3
    assert before['decisions_finalized_count'] == 3
    assert before['decisions_released_count'] == 0
    assert before['override_count'] == 0
    response = school['teacher'].post('/dynamic/school-attempts/' + attempt['attempt_id'] + '/release', json=dict(
        final_correction_id=final['final_correction_id'], release_grade=True, release_feedback=False))
    assert response.status_code == 200, response.text
    after = metrics(school)
    assert after['decisions_finalized_count'] == after['decisions_released_count'] == 3
    assert metrics(school, '/management/classrooms/class-b/overview')['decisions_finalized_count'] == 0
    assert school['clients']('manager.a').get('/management/schools/school-b/overview').status_code == 403
    assert school['student'].get('/management/overview').status_code == 403
    # Aggregates must not expose any individual solution, rubric or score.
    raw = json.dumps(after)
    assert not any(key in raw for key in ('solution_text', 'student_user_id', 'final_points', 'rubric_items'))


def test_reopening_revokes_release_and_invalidates_only_reopened_question(school):
    attempt, final = completed(school)
    eid = attempt['attempt_id']
    assert school['teacher'].post('/dynamic/school-attempts/' + eid + '/release', json=dict(
        final_correction_id=final['final_correction_id'], release_grade=True, release_feedback=False)).status_code == 200
    assert metrics(school)['decisions_released_count'] == 3
    response = school['teacher'].post(f'/tme/exam-submissions/{eid}/correction/reopen', json=dict(
        final_correction_id=final['final_correction_id'], execution_key='management-reopen'))
    assert response.status_code == 200, response.text
    cid = attempt['questions'][0]['case_id']
    workspace = school['teacher'].get('/tme/question-attempts/' + cid + '/workspace').json()
    decision = workspace['current_human_decision']
    response = school['teacher'].post('/tme/cases/' + cid + '/reopen', json=dict(
        human_decision_id=decision['human_decision_id'], execution_key='management-question-reopen'))
    assert response.status_code == 200, response.text
    result = metrics(school)
    assert result['decisions_finalized_count'] == 2
    assert result['decisions_released_count'] == 0


@pytest.mark.parametrize('artifact', ['human_decision', 'release'])
def test_corrupt_decision_or_release_is_unavailable_not_a_false_zero(school, artifact):
    attempt, final = completed(school)
    eid = attempt['attempt_id']
    assert school['teacher'].post('/dynamic/school-attempts/' + eid + '/release', json=dict(
        final_correction_id=final['final_correction_id'], release_grade=True, release_feedback=False)).status_code == 200
    if artifact == 'human_decision':
        path = next((school['root']/'cases'/attempt['questions'][0]['case_id']/'human_decisions').glob('*.json'))
    else:
        path = next((school['root']/'exams'/eid/'school_releases').glob('*.json'))
    path.write_text('{}')  # Deliberate corruption of synthetic temporary data.
    result = metrics(school)
    assert result['decisions_finalized_count'] is None
    assert result['decisions_released_count'] is None
    assert result['override_count'] is None
    assert result['submissions_count'] == 3


def test_tme_confirmation_projection_uses_existing_invalidation_and_scores(exam):
    from test_tme_finalization import populate
    from confia_lean_auditor.submissions.router import store
    from confia_lean_auditor.tme.store import case_store
    from confia_lean_auditor.management.question_decisions import decision_state
    _, _, _, cases = exam
    populate(exam)
    submissions = store()
    states = [decision_state(submissions.get_record(case_store().read(c['case_id']).submission_id), submissions)
              for c in cases]
    assert [s['finalized'] for s in states] == [True, True, True]
    assert [s['override'] for s in states] == [False, True, True]
    assert not any(s['released'] for s in states)


from test_tme_finalization import exam
from test_tme_full_exam import demo
