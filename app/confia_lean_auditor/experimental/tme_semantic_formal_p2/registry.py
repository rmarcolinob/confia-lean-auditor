"""Executable P2 coverage matrix. Descriptions contain no points or solutions."""
from dataclasses import asdict, dataclass
from types import MappingProxyType
from confia_lean_auditor.experimental.tme_p2_checker_first.registry import coverage_rows
from confia_lean_auditor.student_claims.tme2_p2_digital import VOCABULARY
from confia_lean_auditor.student_claims.obligation_catalog import P2

PROBLEM_ID = 'TME2026P2'

@dataclass(frozen=True)
class ObligationSpec:
    obligation_id: str
    rubric_item: str
    description: str
    coverage: str
    route: str
    subjects: tuple[str, ...]
    claim_types: tuple[str, ...]
    checker: str
    sufficiency_policy: str
    subchecks: tuple[str, ...]


def _row(row):
    oid = row['obligation_id']; key = oid.split('.')[1]
    subjects = (key,)
    if key in {'placement', 'complete_configuration'}: subjects = ('placement',)
    if oid in {'a.pairs', 'a.pair_sum'}: subjects = (key, 'pairs', 'placement')
    subjects = tuple(dict.fromkeys(subjects))
    description = (P2.get(key) or 'Pares explicitamente escritos que realizam o centro indicado.'
                   if key not in {'placement','complete_configuration'} else
                   'Posições explicitamente escritas; não inferir coordenadas a partir de prosa ou imagem.')
    route = {'FORMAL_STRONG':'FORMAL','DETERMINISTIC_STRONG':'DETERMINISTIC','COMPOSITE_STRONG':'COMPOSITE'}[row['coverage']]
    subchecks = ('arithmetic','counting_components','relation') if route == 'COMPOSITE' else ('existing_checker',)
    policy = ('all_three_components_verified' if route == 'COMPOSITE' else
              'executed_lean_verified_and_existing_dependencies' if route == 'FORMAL' else 'existing_exact_checker_verified')
    return ObligationSpec(oid, oid[0], description, row['coverage'], route, subjects,
        tuple(sorted({VOCABULARY[s]['kind'] for s in subjects})),row['primary_checker'],policy,subchecks)

REGISTRY = MappingProxyType({r['obligation_id']:_row(r) for r in coverage_rows()})

def registry_rows(): return [asdict(s) for s in REGISTRY.values()]

def require_p2(problem):
    if problem != PROBLEM_ID: raise ValueError('semantic_formal_p2_only')
