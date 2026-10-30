"""Explicit reference obligations, using declared data rather than prose guesses."""
from fractions import Fraction
import re

from confia_lean_auditor.core.schemas import ExtractedClaim
from confia_lean_auditor.core.math_canonical import parse_math
from confia_lean_auditor.student_claims.grounding import local_integer_bindings
from confia_lean_auditor.student_claims.generic_math import math_runs
from confia_lean_auditor.rubric.positive_evidence import rules
from .adapters import claim_from_extracted
from .schemas import ExpectedObligation

# Semantic contracts, independent of problem identifiers and answer values.
DIGIT_OBLIGATIONS = {'final_digit_five': 'leading_digit', 'leading_digit': 'leading_digit',
                     'final_digit': 'leading_digit'}


def exact_integer(text):
    if type(text) is int:return text
    if not isinstance(text,str):return None
    parsed=parse_math(text)
    if parsed.status!='parsed' or parsed.canonical_form.kind!='expression':return None
    tree=parsed.canonical_form.tree
    if tree.kind!='rational':return None
    value=Fraction(tree.value)
    return int(value) if value.denominator==1 else None


def quantity_subject(statement):
    """Only an explicit mathematical operand of the leading-digit question.

    A unique full operand must parse. No numbers are selected from surrounding
    logarithm data and no expression is invented from a vague description.
    """
    values=[]
    pattern=r'primeiro\s+algarismo(?:,\s*da\s+esquerda\s+para\s+a\s+direita,)?\s+(?:do\s+resultado\s+de|de|do)\s+'
    for match in re.finditer(pattern,statement,re.I):
        suffix=statement[match.end():];run=next(math_runs(suffix),None)
        if run and run[0]==0:
            parsed=parse_math(run[2])
            if parsed.status=='parsed':values.append(parsed.canonical_form.to_dict())
    return values[0] if len(values)==1 else None


def annotate(record,item,source,statement):
    subject=quantity_subject(statement) if item.claim_type in DIGIT_OBLIGATIONS else None
    return record.model_copy(update={'expected_obligation':ExpectedObligation(
        criterion_id=item.id,claim_id=record.provenance.legacy_id,claim_type=item.claim_type,
        expected_payload=record.legacy_payload.get('normalized',{}),
        required_microclaim_ids=tuple(item.required_microclaim_ids),representation_source=source,
        quantity_subject=subject)})


def explicit_obligations(*,problem_id,solution_text,rubric_config,correct_answer,statement_text):
    """Return only atomic, complete declarations usable by the existing gate."""
    by_criterion={};sources={}
    for item in rubric_config.items:
        rule=rules().get((problem_id,item.claim_type))
        if rule is None:continue
        payloads=[];source=None
        if rule.binding:
            expected=dict(rule.binding)
            values=local_integer_bindings(correct_answer,tuple(expected)) if isinstance(correct_answer,str) else None
            if values!=expected and len(expected)==1 and exact_integer(correct_answer)==next(iter(expected.values())):
                values=expected
            if values==expected:
                payloads=[values];source='problem.correct_answer + positive_rules.binding'
        elif item.claim_type in DIGIT_OBLIGATIONS:
            digit=exact_integer(correct_answer)
            if digit is not None and 0<=digit<=9:
                payloads=[{'digit':digit}];source='problem.correct_answer + leading_digit semantic contract'
        elif len(rule.requirements)==1 and len(rule.requirements[0].patterns)==1:
            equations=getattr(rule.requirements[0].patterns[0],'equations',())
            if equations:
                payloads=[{'expression':equation} for equation in equations]
                source='positive_rules.explicit_equation'
        records=[]
        for index,payload in enumerate(payloads):
            identifier='expected:'+item.id+(':'+str(index) if index else '')
            record=claim_from_extracted(ExtractedClaim(id=identifier,type=item.claim_type,
                text='Explicit expected mathematical obligation (not student text)',
                evidence='Declared reference data, not a student quotation',confidence=1,
                normalized={k:str(v) for k,v in payload.items()}),problem_id=problem_id,
                solution_text=solution_text,rubric_links=(item.id,))
            if record.canonical_form is not None:
                records.append(annotate(record,item,source,statement_text))
        if records:by_criterion[item.id]=tuple(records);sources[item.id]=source
    return by_criterion,sources
