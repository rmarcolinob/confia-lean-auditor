"""Effective routes are owned by the registry, not the extractor."""
from .obligation_registry import REGISTRY, FORMAL_OBLIGATIONS


class ClaimRouter:
    def route(self, evidence, obligation_id):
        spec = REGISTRY[obligation_id]
        if evidence.claim_type not in spec.allowed_claim_types:
            raise ValueError('claim_type_not_allowed_for_obligation')
        if evidence.verification_route_candidate == 'FORMAL' and obligation_id not in FORMAL_OBLIGATIONS:
            raise ValueError('invented_formal_route')
        if evidence.claim_type == 'qualitative':
            from confia_lean_auditor.core.math_canonical import parse_math
            from confia_lean_auditor.student_claims.digital_literals import literal_form
            if (literal_form(evidence.normalized_claim) is not None
                    or parse_math(evidence.normalized_claim).status == 'parsed'):
                raise ValueError('supported_math_cannot_bypass_checker_as_qualitative')
        route = ('FORMAL' if obligation_id in FORMAL_OBLIGATIONS else
                 'SEMANTIC' if evidence.claim_type == 'qualitative' else 'DETERMINISTIC')
        if route not in spec.allowed_routes:
            raise ValueError('route_not_allowed')
        return route
