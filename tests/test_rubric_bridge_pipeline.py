"""Real offline Lean integration, using a portable class of the V2 conclusion."""
import json
from pathlib import Path

from confia_lean_auditor.main import execute_audit
from confia_lean_auditor.core.schemas import AuditRequest


def test_unsupported_legacy_wording_reaches_rubric_through_verified_student():
    response = execute_audit(AuditRequest(problem_id='ITA2025F2Q1',
        solution='Logo a vale -1 e b vale 3.'))
    assert response.extracted_claims.claims == []
    final = response.rubric_assessment.items[-1]
    assert final.points == 2 and final.claim_id is None
    assert final.positive_evidence['student_bridge']['verification_basis'] == 'formal_lean_verified'
    assert response.evaluated_score == response.evaluated_max_score == 2
    assert response.coverage == 0.2 and response.needs_review
    # The unchanged policy cannot invent the other criteria without an API.
    assert response.score is None and response.unscorable_reason == 'ADJUDICATOR_UNAVAILABLE'
    catalog = json.loads((Path(response.artifact_dir)/'math_claims.json').read_text())
    expected_id = final.positive_evidence['student_bridge']['expected_claim_id']
    expected = next(r for r in catalog['records'] if r['record_id'] == expected_id)
    assert expected['provenance']['origin'] == 'reference_expected'
    assert expected['source']['attributable'] is False
    assert any(a['status'] == 'aligned' and a['reference_record_id'] == expected_id for a in catalog['alignments'])
