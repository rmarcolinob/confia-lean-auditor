"""Explicit translations of existing representations, never a new CAS.

The registry is deliberately partial. Missing translators produce None, not an
inferred expected answer. Mathematical values always come from the legacy data.
"""
from confia_lean_auditor.core.audit_math_projection import canonicalize_equality
from confia_lean_auditor.student_claims.grounding import local_integer_bindings, _scaled
from .schemas import CanonicalForm

# Only atomic pairs with a reliable existing representation are alignable.
PAIRS = {
    ('ITA2025F2Q1', 'final_answer'): 'f2q1_student_final_answer',
    ('ITA2025F2Q3', 'beta_difference'): 'f2q3_student_beta_difference',
    ('ITA2025F2Q5', 'log_power_decomposition'): 'f2q5_student_log_power_decomposition',
    ('ITA2025F2Q5', 'mantissa_identification'): 'f2q5_student_mantissa',
    ('ITA2025F2Q5', 'digit_log_bounds'): 'f2q5_student_digit_log_bounds',
    ('ITA2025F2Q5', 'final_digit_five'): 'f2q5_student_final_digit',
}


def _form(family, subject, variables, value, method):
    return CanonicalForm(family=family, subject=subject, variables=variables, value=value, method=method)


def legacy_canonical_from_legacy(problem_id, channel, payload):
    kind = payload.get('type') if channel == 'extracted' else payload.get('claim_type')
    data = payload.get('normalized', {}) if channel == 'extracted' else payload.get('data', {})
    if channel == 'extracted' and kind in {'final_answer','coefficient_assignment','coefficient_solution'}:
        import re
        values=None
        if data and all(re.fullmatch(r'[A-Za-z]',k) for k in data):
            values=local_integer_bindings('; '.join(f'{k}={v}' for k,v in data.items()),tuple(data))
        elif set(data) in ({'answer'},{'value'}):
            from confia_lean_auditor.rubric.positive_evidence import rules
            rule=rules().get((problem_id,kind))
            if rule and len(rule.binding)==1:
                symbol=rule.binding[0][0]
                values=local_integer_bindings(symbol+'='+str(next(iter(data.values()))),(symbol,))
        if values is not None:
            return _form('integer_bindings','final_answer',tuple(sorted(values)),values,'local_integer_bindings')
    if channel == 'student' and payload.get('claim_type') == 'math_bindings':
        values = data.get('bindings', {})
        if values and all(isinstance(k,str) and type(v) is int for k,v in values.items()):
            return _form('integer_bindings','local_bindings',tuple(sorted(values)),values,'local_integer_bindings')
        return None
    ref_kind = kind if channel == 'extracted' else next(
        (ref for (pid, ref), student in PAIRS.items() if pid == problem_id and student == kind), None)
    try:
        if problem_id == 'ITA2025F2Q1' and ref_kind == 'final_answer':
            if set(data) != {'a', 'b'}:
                return None
            values = local_integer_bindings('; '.join(f'{k}={data[k]}' for k in ('a', 'b')), ('a', 'b'))
            if values is None:
                return None
            # Full literal bindings only; never accept a numeric prefix.
            if any(str(values[k]) != str(data[k]).strip() for k in values):
                return None
            return _form('integer_bindings', 'final_answer', ('a', 'b'), values, 'local_integer_bindings')
        if problem_id == 'ITA2025F2Q3' and ref_kind == 'beta_difference':
            value = data['beta_difference' if channel == 'extracted' else 'value_expr']
            canonical = canonicalize_equality(f'cos(beta)-sin(beta)={value}')
            if canonical is None:
                return None
            return _form('affine_equality', 'beta_difference', ('beta',),
                         [[atom, str(coefficient)] for atom, coefficient in canonical], 'canonicalize_equality')
        if problem_id == 'ITA2025F2Q5':
            fields = {
                'log_power_decomposition': (('total_log', 'total_log_scaled'),),
                'mantissa_identification': (('mantissa', 'mantissa_scaled'),),
                'digit_log_bounds': (('log5', 'log5_scaled'), ('log6', 'log6_scaled')),
            }
            if ref_kind in fields:
                values = {student: _scaled(data[ref]) if channel == 'extracted' else data[student]
                          for ref, student in fields[ref_kind]}
                if not all(type(v) is int for v in values.values()):
                    return None
                return _form('scaled_decimal', ref_kind, (), values, 'grounding._scaled:10000')
            if ref_kind == 'final_digit_five':
                value = local_integer_bindings('d=' + str(data['digit']), ('d',))
                if value is not None and str(value['d']) == str(data['digit']).strip():
                    return _form('integer_binding', 'leading_digit', (), value, 'local_integer_bindings')
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OverflowError):
        return None
    return None


def canonical_details_from_legacy(problem_id, channel, payload):
    """Parse explicit data, never prose, guessed fields or expected answers."""
    from confia_lean_auditor.core.math_canonical import parse_math
    legacy = legacy_canonical_from_legacy(problem_id, channel, payload)
    data = payload.get('normalized', {}) if channel == 'extracted' else payload.get('data', {})
    if channel == 'student' and payload.get('claim_type', '').startswith('math_') and data.get('negated'):
        return None, 'unsupported', 'Explicit negation retained; no positive mathematical proposition inferred'
    if legacy is not None and legacy.family == 'affine_equality':
        value = data.get('beta_difference', data.get('value_expr'))
        parsed = parse_math('cos(beta)-sin(beta)=' + str(value))
        if parsed.status == 'parsed':
            return legacy.model_copy(update={'mathematical_form': parsed.canonical_form.to_dict()}), 'parsed', parsed.reason
        return None, parsed.status, parsed.reason
    if legacy is not None:
        return legacy, 'parsed', 'Exact existing structured representation'
    fields = [(k,v) for k,v in data.items() if k in {'equation','expression','expr','formula_text','value_expr'} and isinstance(v,str)]
    if not fields and len(data)==1:
        fields = [(k,v) for k,v in data.items() if isinstance(v,str)]
    if len(fields)!=1:
        return None, 'unsupported', 'No unique explicit mathematical field in the legacy payload'
    field, text = fields[0]
    parsed = parse_math(text, expected_kind='interval' if field=='interval' else None)
    if parsed.status!='parsed':
        return None, parsed.status, parsed.reason
    form = parsed.canonical_form
    if channel == 'student' and payload.get('claim_type') == 'math_value':
        # A numeric value does not identify its mathematical subject. Keep
        # first/last digit, remainder, answer and explicit subject distinct;
        # the existing aligner must not compare only their bare numbers.
        subject = str(data.get('concept')) + ':' + str(data.get('subject_text', ''))
        return CanonicalForm(family='explicit_semantic_value', subject=subject,
            variables=form.variables, value=form.to_dict(), method='parse_math'), 'parsed', parsed.reason
    return CanonicalForm(family='mathematical', subject=field, variables=form.variables,
                         value=form.to_dict(), method='parse_math'), 'parsed', parsed.reason


def canonical_from_legacy(problem_id, channel, payload):
    return canonical_details_from_legacy(problem_id, channel, payload)[0]


def mathematical_value(form):
    if form is None:
        return None
    return form.mathematical_form or (form.value if form.family=='mathematical' else None)
