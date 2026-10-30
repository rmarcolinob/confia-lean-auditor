"""Conservative content alignment; no matching by wording or rubric score."""

from .adapters import validate_projection
from .canonical import PAIRS, mathematical_value
from confia_lean_auditor.core.math_canonical import compare_canonical
from confia_lean_auditor.core.math_canonical.models import canonical_from_dict, EquivalenceResult
from .schemas import ClaimAlignment
from .compatibility import project_pair, compare as compare_projected


def align_claims(reference, students, *, solution_text, statement_text=''):
    def result(status, reason, candidates=(), preferred=(), basis=None):
        return ClaimAlignment(reference_record_id=reference.record_id,
            student_record_ids=tuple(c.record_id for c in candidates), status=status,
            preferred_attribution_ids=tuple(c.record_id for c in preferred), reason=reason, alignment_basis=basis)
    try:
        validate_projection(reference, solution_text=solution_text, statement_text=statement_text)
    except ValueError:
        return result('ambiguous', 'Reference projection is inconsistent')
    if reference.provenance.channel != 'extracted':
        return result('unmatched', 'Alignment requires a reference candidate and student candidates')
    student_type = PAIRS.get((reference.problem_id, reference.claim_type), reference.claim_type)
    candidates = [c for c in students if c.problem_id == reference.problem_id and
                  c.provenance.channel == 'student' and c.claim_type == student_type]
    strict_ids={c.record_id for c in candidates}
    expanded=[]
    for candidate in students:
        if (candidate.problem_id==reference.problem_id and candidate.provenance.channel=='student'
                and candidate.record_id not in strict_ids and candidate.claim_type.startswith('math_')):
            if project_pair(reference,candidate,statement_text=statement_text) is not None:
                expanded.append(candidate)
    candidates+=expanded
    if not candidates:
        return result('unmatched', 'No supported cross-channel representation pair')
    try:
        for candidate in candidates:
            validate_projection(candidate, solution_text=solution_text, statement_text=statement_text)
    except ValueError:
        return result('ambiguous', 'Student projection is inconsistent', candidates)
    if len({c.record_id for c in candidates}) != len(candidates):
        return result('ambiguous', 'Duplicate record identities', candidates)
    if any(c.source.grounding_status == 'ambiguous' for c in candidates):
        return result('ambiguous', 'At least one candidate has ambiguous grounding', candidates)
    grounded = [c for c in candidates if c.source.attributable and c.source.grounding_status == 'grounded']
    if not grounded:
        return result('unmatched', 'No attributable grounded student content', candidates)
    if reference.canonical_form is None or any(c.canonical_form is None for c in grounded):
        return result('unmatched', 'Canonical form unavailable; attribution still belongs to grounded source', candidates, grounded)
    if expanded:
        pairs=[project_pair(reference,c,statement_text=statement_text,strict=c.record_id in strict_ids) for c in grounded]
        if any(p is None for p in pairs):
            return result('unmatched','No safe common projection for all competing candidates',candidates,grounded)
        if any(compare_projected(pairs[0][1],p[1]).status!='equivalent' for p in pairs[1:]):
            return result('ambiguous','Grounded competing interpretations disagree or remain unknown',candidates,grounded)
        comparisons=[compare_projected(*p) for p in pairs]
        if any(c.status=='not_equivalent' for c in comparisons):
            return result('conflicting','Grounded content contradicts the same structured obligation',candidates,grounded,comparisons[0].basis)
        if any(c.status=='unknown' for c in comparisons):
            return result('unmatched','Mathematical equivalence is unknown; no unsafe fallback',candidates,grounded)
        return result('aligned','Complete mathematical payloads agree across compatible semantic contracts',candidates,grounded,comparisons[0].basis)
    def compare(a, b):
        ma, mb = mathematical_value(a), mathematical_value(b)
        if ma is not None and mb is not None:
            return compare_canonical(canonical_from_dict(ma), canonical_from_dict(mb))
        if a.family == b.family and a.subject == b.subject and a.variables == b.variables:
            return EquivalenceResult('equivalent' if a.value == b.value else 'not_equivalent',
                                     'Exact structured values', 'structured_values')
        return EquivalenceResult('unknown', 'No comparable mathematical representation')
    if any(compare(grounded[0].canonical_form, c.canonical_form).status != 'equivalent' for c in grounded[1:]):
        return result('ambiguous', 'Grounded candidates disagree or cannot be compared; none is selected', candidates, grounded)
    comparisons = [compare(reference.canonical_form, c.canonical_form) for c in grounded]
    if any(c.status == 'not_equivalent' for c in comparisons):
        return result('conflicting', 'Grounded student content differs from the reference; retain both origins', candidates, grounded, comparisons[0].basis)
    if any(c.status == 'unknown' for c in comparisons):
        return result('unmatched', 'Mathematical equivalence is unknown; grounded attribution is retained', candidates, grounded)
    return result('aligned', 'Supported mathematical content agrees; this is not a proof of correctness', candidates, grounded, comparisons[0].basis)


def align_obligations(references,students,*,solution_text,statement_text=''):
    """Resolve cross-obligation ambiguity before any rubric item consumes credit."""
    results=[align_claims(r,students,solution_text=solution_text,statement_text=statement_text) for r in references]
    ids=[r.record_id for r in references]
    if len(set(ids))!=len(ids):
        return tuple(r.model_copy(update={'status':'ambiguous','reason':'Duplicate expected record identities'}) for r in results)
    owners={}
    for reference,result in zip(references,results):
        if result.status=='aligned':
            for student_id in result.preferred_attribution_ids:
                owners.setdefault(student_id,set()).update(reference.rubric_links or (reference.record_id,))
    ambiguous={student_id for student_id,criteria in owners.items() if len(criteria)>1}
    return tuple(result.model_copy(update={'status':'ambiguous',
        'reason':'Student content fits multiple distinct rubric obligations; no silent selection'})
        if result.status=='aligned' and ambiguous.intersection(result.preferred_attribution_ids) else result
        for result in results)
