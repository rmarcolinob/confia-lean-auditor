"""Bounded exact checks over the shared canonical grammar, never generated code.

Polynomial comparison is univariate, degree <= 12, rational coefficients <= 512
bits. A checked identity/root set says nothing about the prose interpretation.
"""
from fractions import Fraction
from confia_lean_auditor.core.math_canonical import parse_math, equivalent
from confia_lean_auditor.core.math_canonical.rational import rational_value
from .preparation_models import CheckResult, CandidateCheck, PreparationAnalysis, Warning, StrategyCheck

VERSION = 'dynamic-exact-polynomial.v1'
SCOPE = 'Apenas expressão declarada, polinômio univariado racional; não certifica interpretação, hipóteses ou solução inteira.'


def bounded(p):
    p = {k: v for k, v in p.items() if v}
    if any(k > 12 or max(v.numerator.bit_length(), v.denominator.bit_length()) > 512 for k, v in p.items()):
        raise ValueError('polynomial budget')
    return p


def add(a, b, sign=1):
    p = dict(a)
    for k, v in b.items(): p[k] = p.get(k, Fraction(0)) + sign * v
    return bounded(p)


def multiply(a, b):
    p = {}
    for i, x in a.items():
        for j, y in b.items(): p[i+j] = p.get(i+j, Fraction(0)) + x*y
    return bounded(p)


def polynomial(text, variable):
    parsed = parse_math(text)
    if parsed.status != 'parsed' or parsed.canonical_form.kind != 'expression':
        raise ValueError('unsupported expression')
    def convert(node):
        if node.kind == 'rational': return bounded({0: Fraction(node.value)})
        if node.kind == 'variable' and node.value == variable: return {1: Fraction(1)}
        if node.kind == 'negative': return {k:-v for k,v in convert(node.args[0]).items()}
        if node.kind in {'sum', 'difference', 'product', 'quotient', 'power'}:
            a = convert(node.args[0])
            if node.kind == 'power':
                exp = node.args[1]
                if exp.kind != 'rational' or Fraction(exp.value).denominator != 1 or not 0 <= int(exp.value) <= 12:
                    raise ValueError('power budget')
                result = {0: Fraction(1)}
                for _ in range(int(exp.value)): result = multiply(result, a)
                return result
            b = convert(node.args[1])
            if node.kind == 'sum': return add(a,b)
            if node.kind == 'difference': return add(a,b,-1)
            if node.kind == 'product': return multiply(a,b)
            if set(b) == {0}: return bounded({k:v/b[0] for k,v in a.items()})
        raise ValueError('outside univariate rational scope')
    return convert(parsed.canonical_form.tree)


def root_set(spec):
    p = add(polynomial(spec.left, spec.variable), polynomial(spec.right, spec.variable), -1)
    values = [rational_value(v) for v in spec.values]
    if not p or not values or None in values or len(set(values)) != len(values):
        return None
    # Divide by every supplied linear factor, including multiplicities. No
    # unexamined factor may remain: substitution alone cannot prove completeness.
    remaining = dict(p)
    for root in values:
        divided = False
        while max(remaining, default=0) > 0:
            degree = max(remaining)
            q, remainder = {}, dict(remaining)
            for k in range(degree, 0, -1):
                coefficient = remainder.get(k, Fraction(0))
                q[k-1] = coefficient
                remainder[k] = 0
                remainder[k-1] = remainder.get(k-1, Fraction(0)) + root * coefficient
            if remainder.get(0, 0): break
            divided = True; remaining = bounded(q)
        if not divided: return False
    return max(remaining, default=0) == 0


def check_claim(claim):
    spec = claim.check
    capability = claim.proposed_verifier
    # Capability selection belongs to the server, not the model's label.
    if spec.kind == 'ROOT_SET': capability = 'DETERMINISTIC'
    elif spec.kind == 'EQUALITY':
        capability = 'EXACT_ARITHMETIC' if rational_value(spec.left) is not None and rational_value(spec.right) is not None else 'SYMBOLIC_ALGEBRA'
    available = capability in {'EXACT_ARITHMETIC', 'SYMBOLIC_ALGEBRA', 'DETERMINISTIC'}
    status, detail = 'UNVERIFIED', 'Verificação não executada: capacidade ou expressão fora do escopo DY2.'
    if available:
        try:
            result = None
            if spec.kind == 'EQUALITY':
                left, right = rational_value(spec.left), rational_value(spec.right)
                if left is not None and right is not None:
                    result = left == right
                elif spec.variable:
                    result = polynomial(spec.left, spec.variable) == polynomial(spec.right, spec.variable)
                else:
                    parsed = [parse_math(text) for text in (spec.left, spec.right)]
                    variables = {v for p in parsed if p.status == 'parsed' for v in p.canonical_form.variables}
                    if len(variables) == 1:
                        variable = next(iter(variables))
                        result = polynomial(spec.left, variable) == polynomial(spec.right, variable)
                    else:
                        comparison = equivalent(spec.left, spec.right)
                        if comparison.status != 'unknown': result = comparison.status == 'equivalent'
            elif spec.kind == 'ROOT_SET': result = root_set(spec)
            if result is not None:
                status = 'VERIFIED_WITHIN_SCOPE' if result else 'CONTRADICTED'
                detail = 'Checagem exata executada: ' + ('igualdade/conjunto completo confirmado.' if result else 'afirmação contradita.')
        except (ValueError, OverflowError, ZeroDivisionError, RecursionError):
            pass
    return CheckResult(claim_id=claim.claim_id, capability=capability,
        reason=claim.verifier_reason, available=available, requires_additional_input=status == 'UNVERIFIED',
        status=status, detail=detail, scope=SCOPE, verifier_version=VERSION)


def warning(code, message):
    return Warning(code=code, message=message, requires_review=True)


def analyze(proposal):
    checks = tuple(check_claim(c) for s in proposal.candidate_reference_solutions for c in s.claims)
    by_id = {c.claim_id:c for c in checks}
    warnings = list(proposal.warnings)
    if any(a.source == 'INFERRED' for a in proposal.assumptions):
        warnings.append(warning('INFERRED_ASSUMPTION', 'Há hipótese inferida; confirme ou reformule o enunciado.'))
    if proposal.uncertainties:
        warnings.append(warning('INTERPRETATION_UNCERTAIN', 'Interpretação com incertezas: ' + '; '.join(proposal.uncertainties)))
    if not proposal.candidate_reference_solutions:
        warnings.append(warning('NO_CANDIDATE', 'Não há solução candidata suficiente; revisão docente necessária.'))
    candidates, signatures = [], []
    for solution in proposal.candidate_reference_solutions:
        local = [by_id[c.claim_id] for c in solution.claims]
        final = solution.final_result
        claims = {c.claim_id:c for c in solution.claims}
        verified = False
        if final.kind == 'ROOT_SET' and final.values:
            values = [rational_value(v) for v in final.values]
            if None not in values:
                signatures.append(('roots', tuple(sorted(set(values)))))
                verified = any(by_id[k].status == 'VERIFIED_WITHIN_SCOPE' and claims[k].check.kind == 'ROOT_SET'
                    and set(values) == {rational_value(v) for v in claims[k].check.values}
                    for k in final.supporting_claim_ids)
        elif final.kind == 'EXPRESSION' and len(final.values) == 1:
            value = rational_value(final.values[0])
            if value is not None:
                signatures.append(('value', value))
                verified = any(by_id[k].status == 'VERIFIED_WITHIN_SCOPE' and claims[k].check.kind == 'EQUALITY'
                    and rational_value(claims[k].check.right) == value for k in final.supporting_claim_ids)
        else:
            signatures.append((final.kind, final.text.strip().casefold()))
        if any(c.status == 'CONTRADICTED' for c in local):
            status = 'CONTRADICTED'
            warnings.append(warning('CONTRADICTED_CLAIM', 'Claim contradito na solução ' + solution.solution_id))
        elif verified and local and all(c.status == 'VERIFIED_WITHIN_SCOPE' for c in local): status = 'VERIFIED_WITHIN_SCOPE'
        elif any(c.status == 'VERIFIED_WITHIN_SCOPE' for c in local): status = 'PARTIALLY_VERIFIED'
        else: status = 'UNRESOLVED'
        if not verified:
            warnings.append(warning('FINAL_RESULT_UNVERIFIED', 'Resultado final não corroborado pelos claims verificados: ' + solution.solution_id))
        if solution.uncertainties:
            warnings.append(warning('CANDIDATE_UNCERTAIN', solution.solution_id + ': ' + '; '.join(solution.uncertainties)))
        if proposal.expects_unique_result and len(set(final.values)) > 1:
            warnings.append(warning('EXPECTED_UNIQUE_RESULT', 'Foram propostas múltiplas respostas apesar da unicidade esperada.'))
        if final.kind in {'NO_SOLUTION', 'NON_UNIQUE', 'UNKNOWN'}:
            warnings.append(warning('RESULT_REQUIRES_REVIEW', 'Ausência, multiplicidade ou indeterminação de resposta exige revisão.'))
        candidates.append(CandidateCheck(solution_id=solution.solution_id, status=status, final_result_verified=verified))
    if len(set(signatures)) > 1:
        warnings.append(warning('INCOMPATIBLE_RESULTS', 'As soluções candidatas têm resultados diferentes; não foi escolhida uma vencedora.'))
    # Completeness of natural-language interpretation is never certified here.
    warnings.append(Warning(code='SCOPE_LIMIT', message=SCOPE + ' Lean: FORMAL_NOT_ATTEMPTED.', requires_review=False))
    strategies = []
    for strategy in proposal.alternative_strategies:
        statuses = [by_id[k].status for k in strategy.expected_key_claim_ids]
        status = ('CONTRADICTED' if 'CONTRADICTED' in statuses else 'VERIFIED_WITHIN_SCOPE' if statuses and all(s == 'VERIFIED_WITHIN_SCOPE' for s in statuses)
            else 'PARTIALLY_VERIFIED' if 'VERIFIED_WITHIN_SCOPE' in statuses else 'UNRESOLVED')
        strategies.append(StrategyCheck(strategy_id=strategy.strategy_id,status=status))
    return PreparationAnalysis(verifier_plan=checks, candidate_checks=tuple(candidates), strategy_checks=tuple(strategies), warnings=tuple(warnings),
        trust_state='HUMAN_REVIEW_REQUIRED' if any(w.requires_review for w in warnings) else 'CHECKED_WITHIN_SCOPE')
