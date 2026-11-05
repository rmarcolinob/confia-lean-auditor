"""Real Lean executions through C1 and the unchanged P1 checkers. No mocks."""
import json
from pathlib import Path
import pytest

from test_tme_semantic_formal_c1 import claim, run


@pytest.mark.parametrize('span,status,score', [
    ('731-137=594', 'FORMAL_VERIFIED', 3),
    ('731-137=584', 'FORMAL_REFUTED', 2),
])
def test_real_p1_a_positive_and_refutation(span, status, score, tmp_path):
    text = '(a)\n' + span
    c = claim(text, span, ['a.identifies_137', 'a.constructs_subtraction', 'a.result_594', 'a.arithmetic_error_only'])
    result = run(text, [c], use_lean=True)
    proof = next(r for r in result['verification_results'] if r['obligation_id'] == 'a.result_594')
    assert proof['status'] == status and result['score'] == score
    check = proof['checker_result']
    assert check['method'] == 'norm_num' and not result['technical_uncertainty']
    if status == 'FORMAL_VERIFIED':
        assert check['compiled'] and check['formal_status'] == 'verified'
        assert Path(check['lean_file']).is_file()
    else:
        assert check['refutation_verified'] and check['formal_status'] == 'refuted'
        assert Path(check['refutation_lean_file']).is_file()
        assert '¬ (' in Path(check['refutation_lean_file']).read_text()
        assert not next(a for a in result['awards'] if a['obligation_id'] == 'a.result_594')['eligible']
    (tmp_path/'real-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(dict(obligation='a.result_594', status=proof['status'], checker=check), ensure_ascii=False))


def test_real_p1_d_counting_equality(tmp_path):
    pairs = '(a,c) ∈ {(7,1),(8,2),(9,3)}'
    choices = 'b ∈ {0,1,2,3,4,5,6,7,8,9}'
    text = '(d)\n' + '\n'.join([pairs, choices, '3*10=30'])
    cs = [claim(text, pairs, ['d.digit_pairs'], kind='collection'),
          claim(text, choices, ['d.middle_choices'], kind='collection'),
          claim(text, '3*10=30', ['d.total_thirty'])]
    result = run(text, cs, use_lean=True)
    proof = next(r for r in result['verification_results'] if r['obligation_id'] == 'd.total_thirty')
    assert proof['status'] == 'FORMAL_VERIFIED'
    check = proof['checker_result']
    assert check['compiled'] and check['formal_status'] == 'verified'
    assert Path(check['lean_file']).is_file()
    assert len(proof['prerequisite_evidence_ids']) == 2
    assert result['score'] == 4 and not result['technical_uncertainty']
    assert any(c['rule_id'] == 'd.count' and c['points'] == 2 for c in result['formal_awards'])
    (tmp_path/'real-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(dict(obligation='d.total_thirty', status=proof['status'], checker=check), ensure_ascii=False))
