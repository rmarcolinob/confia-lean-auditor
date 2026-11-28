"""Curricular integration matrix; synthetic opinions are NOT human gold or live LLM validation."""
import json
from pathlib import Path
import pytest
from test_dynamic_dy3 import setup
from test_dynamic_credit_dependencies import flow, partial, opinion

CORPUS = json.loads((Path(__file__).parent/'fixtures/dynamic_highschool_topics.json').read_text())


@pytest.mark.parametrize('case', CORPUS, ids=lambda c:c['topic'])
@pytest.mark.parametrize('variant,state,level,expected', [
    ('correct','met',None,'2'), ('partial','partial','initial','1'),
    ('incorrect','not_met',None,'0'), ('alternative','met',None,'2'),
    ('correct','review',None,None), ('correct','error',None,None),
])
def test_novel_school_problems_use_shared_semantic_services(setup,monkeypatch,case,variant,state,level,expected):
    criteria = [partial('reasoning',2)]
    criteria[0]['description'] = 'Justificar a resolução e sua conclusão com argumentos matemáticos válidos.'
    _, question, run, review, rec, calls = flow(setup,monkeypatch,criteria,
        {'reasoning':opinion(state,level)}, statement=case['statement'], solution=case[variant])
    assert run.problem_id.startswith('dyn_')
    assert rec['reconciled_suggested_score'] == expected
    assert run.result.score == (None if expected is None else float(expected))
    assert {'grader','independent_reviewer'} <= {c['stage'] for c in calls}
    assert all(c['solution'] == case[variant] for c in calls)
    assert all('reference_score' not in c and 'gold' not in c for c in calls)
    assert not run.result.analysis.provenance['llm_used']
    assert run.result.decisions[0].semantic_trace['formal_certification'] is False
    if state == 'error':
        assert rec['technical_uncertainty']
    if expected is None:
        assert rec['review_required']
    # The problem ID and approved rubric are generated through the ordinary
    # services. No problem-specific Python checker or Lean theorem is registered.
    assert question['dynamic_context']['rubric_sha256'] == run.result.context.rubric_sha256


@pytest.mark.parametrize('case', CORPUS, ids=lambda c:c['topic'])
def test_disabled_provider_keeps_novel_reasoning_pending(setup,monkeypatch,case):
    from test_dynamic_credit_dependencies import problem
    from test_dynamic_dy3 import attempt
    from test_dynamic_semantic_consistency import review_and_reconcile
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY','dynamic-semantic.v1')
    monkeypatch.setenv('CONFIA_SEMANTIC_LLM_ENABLED','0')
    monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','0')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    _, client = setup
    document = problem([partial('reasoning',2)],statement=case['statement'])
    question, base, body = attempt(client,document,case['correct'])
    response = client.post(base+'/audits',json=body)
    assert response.status_code == 200,response.text
    run=response.json()
    assert run['status'] == 'COMPLETED'  # Technical execution, not a final grade.
    assert run['result']['score'] is None
    assert not run['result']['analysis']['provenance']['llm_used']
    review,rec=review_and_reconcile(client,question,run,profile='SCHOOL_EXAM')
    assert rec['reconciled_suggested_score'] is None and rec['review_required']
    assert rec['technical_uncertainty']
