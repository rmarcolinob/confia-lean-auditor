"""Routing derived from the frozen thirteen-obligation coverage, never the LLM."""
from dataclasses import asdict, dataclass
from types import MappingProxyType
from confia_lean_auditor.experimental.tme_p3_checker_first.registry import coverage_rows
from confia_lean_auditor.student_claims.tme2_p3_digital import VOCABULARY

PROBLEM_ID = 'TME2026P3'
SUBJECTS = {
 'a.bottom_white_count': ('inferiores_brancas',),
 'a.first_white_probability': ('primeira_branca',),
 'b.ordered_pairs': ('pares_ordenados',),
 'b.different_favorable': ('favoraveis_distintos',),
 'b.same_compartment': ('repeticao_branca',),
 'b.second_white_probability': ('segunda_branca','arvore_total'),
 'b.alternative_complete': ('arvore_total',*(f'ramo_{i}' for i in range(1,7))),
 'c.continue_compartments': ('continuar',),
 'c.strategy_case_1': ('estrategia_1','contagem_1'),
 'c.strategy_case_2': ('estrategia_2','contagem_2'),
 'c.conditional_success_1': ('condicional_1',),
 'c.conditional_success_2': ('condicional_2',),
 'c.total_win_probability': ('total',),
}
DESCRIPTIONS = (
 'Contagem explicitamente atribuída às bolas brancas inferiores.',
 'Probabilidade da primeira bola branca; resultado isolado permitido.',
 'Espaço amostral de pares ordenados e relação de duas escolhas.',
 'Relação de contagem dos favoráveis com compartimentos diferentes.',
 'Compartimentos que liberam branca ao repetir a escolha.',
 'Probabilidade da segunda branca; distinguir resultado de desenvolvimento.',
 'Árvore condicional completa com ramos e soma ponderada escritos.',
 'Compartimentos após os quais o jogo continua.',
 'Cor ótima e contagem após primeira retirada do compartimento 1.',
 'Cor ótima e contagem após primeira retirada do compartimento 2.',
 'Probabilidade condicional de sucesso no caso 1 com estratégia.',
 'Probabilidade condicional de sucesso no caso 2 com estratégia.',
 'Probabilidade global de vitória com contexto e desenvolvimento.',
)

@dataclass(frozen=True)
class ObligationSpec:
    obligation_id: str
    rubric_item: str
    description: str
    coverage: str
    route: str
    allowed_routes: tuple[str,...]
    subjects: tuple[str,...]
    claim_types: tuple[str,...]
    checker: str
    sufficiency_policy: str

def _rows():
    for row, description in zip(coverage_rows(), DESCRIPTIONS):
        oid=row['obligation_id']; subjects=SUBJECTS[oid]
        route='COMPOSITE' if row['coverage']=='COMPOSITE_STRONG' else 'DETERMINISTIC'
        allowed=('DETERMINISTIC','FORMAL') if oid=='a.first_white_probability' else (route,)
        yield ObligationSpec(oid,oid[0],description,row['coverage'],route,allowed,subjects,
              tuple(sorted({VOCABULARY[s]['kind'] for s in subjects})),row['primary_checker'],
              'frozen_checker_first_with_result_method_separation')

REGISTRY=MappingProxyType({s.obligation_id:s for s in _rows()})

def registry_rows(): return [asdict(s) for s in REGISTRY.values()]

def require_p3(problem):
    if problem!=PROBLEM_ID: raise ValueError('semantic_formal_p3_only')

def route_for_expression(oid,expression):
    if oid=='a.first_white_probability' and '=' in expression: return 'FORMAL'
    return REGISTRY[oid].route
