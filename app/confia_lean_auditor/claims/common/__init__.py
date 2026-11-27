"""Gradual common claim layer; legacy schemas and proof semantics remain intact."""
from .schemas import MathClaimRecord, MathClaimCatalog, Origin, SemanticRole
from .adapters import claim_from_extracted, claim_from_student
from .alignment import align_claims

__all__ = ['MathClaimRecord', 'MathClaimCatalog', 'Origin', 'SemanticRole',
           'claim_from_extracted', 'claim_from_student', 'align_claims']
