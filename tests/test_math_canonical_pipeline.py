"""A real offline Lean audit with an algebraically rearranged F2Q3 fixture."""
import json
from pathlib import Path

from confia_lean_auditor.main import execute_audit
from confia_lean_auditor.core.schemas import AuditRequest
from confia_lean_auditor.claims.common import MathClaimCatalog


def test_shifted_f2q3_equation_keeps_full_credit_and_formal_checks():
    original=Path('problems/ITA2025F2Q3/examples/correct_solution.txt').read_text()
    solution=original.replace('cos beta - sen beta = 1/2','cos beta = sen beta + 1/2')
    assert solution!=original
    result=execute_audit(AuditRequest(problem_id='ITA2025F2Q3',solution=solution))
    assert result.score==10 and result.verdict=='correto'
    beta=next(i for i in result.rubric_assessment.items if i.id=='beta_difference')
    assert beta.points==2
    assert beta.positive_evidence['source_spans'][0]['alignment_basis']=='canonical_equivalence'
    assert any(c['claim_type']=='f2q3_student_beta_difference' and c['status']=='verified'
               for c in result.student_claim_checks)
    path=Path(result.artifact_dir)/'math_claims.json'
    catalog=MathClaimCatalog.model_validate_json(path.read_text())
    student=next(r for r in catalog.records if r.claim_type=='f2q3_student_beta_difference')
    assert student.canonicalization_status=='parsed' and student.canonical_form.mathematical_form
    assert student.source.raw_text in solution
    assert any(a.alignment_basis=='canonical_equivalence' and student.record_id in a.preferred_attribution_ids
               for a in catalog.alignments)
    assert json.loads(path.with_name('audit.json').read_text())==result.model_dump(mode='json')
