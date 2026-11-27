"""Generic source evidence reaches artifacts without manufacturing a proof."""
import json
from pathlib import Path

from confia_lean_auditor.core.schemas import AuditRequest
from confia_lean_auditor.main import execute_audit


def test_generic_digit_reaches_catalog_with_expected_value_credit_without_artificial_lean():
    text='O primeiro algarismo de 3^100, da esquerda para a direita, é 5.'
    response=execute_audit(AuditRequest(problem_id='ITA2025F2Q5',solution=text))
    catalog=json.loads((Path(response.artifact_dir)/'math_claims.json').read_text())
    digit=next(r for r in catalog['records'] if r['legacy_payload'].get('data',{}).get('concept')=='leading_digit')
    assert digit['legacy_payload']['data']['expression']=='5'
    assert digit['source']['grounding_status']=='grounded' and digit['source']['attributable']
    assert digit['provenance']['extraction_method']=='generic_math'
    assert digit['verification_results']==[]
    assert all(not c['claim_type'].startswith('math_') for c in response.student_claim_checks)
    final=response.rubric_assessment.items[-1]
    assert final.id=='final_digit' and final.points==2
    bridge=final.positive_evidence['student_bridge']
    assert bridge['alignment']['status']=='aligned'
    assert bridge['alignment_basis']=='structured_equivalence'
    assert bridge['verification_basis']=='deterministic_expected_value'
    assert all(item.points is None for item in response.rubric_assessment.items[:-1])
    trace=next(t for t in catalog['criterion_traces'] if t['criterion_id']=='final_digit')
    assert trace['reference_record_id']==bridge['expected_claim_id']
    assert digit['record_id'] in trace['student_record_ids']
