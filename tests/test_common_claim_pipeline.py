"""Real offline Lean integration for the additive common-claim artifact."""
import json
from pathlib import Path

import pytest

from confia_lean_auditor.main import execute_audit
from confia_lean_auditor.core.schemas import AuditRequest
from confia_lean_auditor.claims.common import MathClaimCatalog, Origin
from confia_lean_auditor.claims.common.bridges import record_is_mathematically_refuted


@pytest.mark.parametrize('correct',[True,False])
def test_common_catalog_preserves_real_pipeline_credit_and_attribution(correct):
    solution=Path('problems/ITA2025F2Q1/examples/correct_solution.txt').read_text() if correct else 'Portanto a=3 e b=2.'
    response=execute_audit(AuditRequest(problem_id='ITA2025F2Q1',solution=solution))
    directory=Path(response.artifact_dir)
    catalog=MathClaimCatalog.model_validate_json((directory/'math_claims.json').read_text())
    public=response.model_dump(mode='json')
    assert 'math_claims' not in public and 'common_claims' not in public
    assert json.loads((directory/'audit.json').read_text())==public
    # Every pointer resolves to an actual existing legacy result; no proof output
    # or score is reconstructed inside the common artifact.
    for record in catalog.records:
        for verification in record.verification_results:
            node=public
            for part in verification.artifact_ref.split('#/',1)[1].split('/'):
                node=node[int(part)] if isinstance(node,list) else node[part]
            assert node is not None
    final=next(i for i in response.rubric_assessment.items if i.id=='final_answer')
    student=next(r for r in catalog.records if r.claim_type=='f2q1_student_final_answer')
    assert student.provenance.origin==Origin.STUDENT_EXPLICIT
    if correct:
        assert response.score==10 and response.verdict=='correto'
        assert final.points==2
        aligned=[a for a in catalog.alignments if a.status=='aligned']
        assert any(student.record_id in a.preferred_attribution_ids for a in aligned)
        assert any(v.status=='verified' and v.attributed_to_student for v in student.verification_results)
    else:
        assert response.score is None and response.verdict=='inconclusivo'
        assert final.points==0 and final.mathematical_status=='refuted'
        assert student.canonical_form.value=={'a':3,'b':2}
        check=next(c for c in response.student_claim_checks if c['claim_type']==student.claim_type)
        assert record_is_mathematically_refuted(student,check,solution_text=solution)
