"""Conservative source adapters. No expected answers, scores or model truth flags."""
import re
from confia_lean_auditor.student_claims.semantic import sha, normalized, supplement_scope
from confia_lean_auditor.tme.obligation_experiment import deterministic_only
from confia_lean_auditor.student_claims.tme2_p3_digital import collect_tme2_p3_digital, VOCABULARY
from .evidence import EvidenceUnit
from .mapper import source_view, representation, _anchor
from .registry import REGISTRY


def clause_view(document, e):
    """Resolve asserted_content within its envelope, retaining its sentence context.

    In particular, expanding an envelope across a correction does not move the
    assertion. Multiple identical occurrences are ambiguous, never last-wins.
    """
    if (document.text[e.source_start:e.source_end] != e.source_span
            or e.metadata.get('source_sha256') != sha(document.text)):
        raise ValueError('invalid_source_binding')
    hits = list(re.finditer(re.escape(e.asserted_content), e.source_span))
    if len(hits) != 1:
        raise ValueError('ambiguous_assertion_location')
    a = e.source_start + hits[0].start(); b = a + len(e.asserted_content)
    # A model may intentionally assert several clauses; never trim those.
    start, end = document.ranges.get(e.item_id, (0, 0))
    if not start <= a < b <= end:
        raise ValueError('invalid_item_binding')
    from .segmentation import BOUNDARY
    breaks = list(BOUNDARY.finditer(document.text[start:end]))
    left = max([start] + [start+m.end() for m in breaks if start+m.end() <= a])
    right = min([end] + [start+m.end() for m in breaks if start+m.start() >= b])
    if document.text[b-1:b] in '.!?': right = b
    while left < a and document.text[left].isspace(): left += 1
    while right > b and document.text[right-1].isspace(): right -= 1
    return e.model_copy(update=dict(source_start=left, source_end=right,
        source_span=document.text[left:right], metadata=dict(e.metadata,
        assertion_range=[a,b], envelope_range=[e.source_start,e.source_end])))


def member_atom(e):
    """A partial inclusion is not a complete set; numbers must name compartments."""
    if re.search(r'\b(?:um|uma)\s+compartimento\s+(?:tambem|da|libera|produz|fornece)\b',normalized(e.asserted_content)):
        return None  # Indefinite article is not compartment index one.
    raw = source_view(e.asserted_content)
    context=source_view(e.source_span)
    if re.search(r'\b(?:nao|nunca|jamais)\b',context):return None
    indices={n for pair in re.findall(r'compartimento\s+([1-6])\b|\b([1-6])(?:\s+compartimento)?\s+tambem',raw) for n in pair if n}
    if len(indices)>1:return None
    if e.item_id == 'b' and e.subject in {'repeticao_branca','unmapped'} and 'b.same_compartment' in e.obligation_candidates:
        explicit=bool(re.search(r'repet|mesmo compartimento',context) and re.search(r'branc',context))
        if not explicit and not e.metadata.get('membership_relation_support'):return None
        match = re.search(r'\b(?:compartimento\s+)?([1-6])(?:\s+compartimento)?\s+tambem(?:\s+(?:libera|produz|fornece)\s+(?:(?:1|uma)\s+)?(?:bola\s+)?branca)?\s*(?=[.;\n]|$)', raw)
        if not match and re.search(r'repet|mesmo compartimento',raw):
            match = re.search(r'\bcompartimento\s+([1-6])\s+(?:tambem\s+)?(?:da|libera|produz|fornece)\s+(?:uma\s+bola\s+)?branca\b',raw)
        if match:
            return dict(property='repeticao_branca', kind='member', members=[int(match[1])],
                        obligation_id='b.same_compartment')
    if e.item_id == 'c' and e.subject in {'continuar','unmapped'} and 'c.continue_compartments' in e.obligation_candidates and re.search(r'continu|mantenho o jogo em curso', raw):
        match = re.search(r'\bcompartimento\s+([1-6])\b', raw)
        if match and not re.search(r'somente|apenas|\{', raw):
            return dict(property='continuar', kind='member', members=[int(match[1])],
                        obligation_id='c.continue_compartments')
    return None


def exact_members(e):
    raw = source_view(e.source_span)
    if re.search(r'\b(?:nao|nunca|jamais)\b',raw):return None
    if e.subject not in {'repeticao_branca','continuar'}:
        return None
    typed = re.search(r'\b'+e.subject+r'\s*:\s*\{(\d+(?:\s*,\s*\d+)*)\}', raw)
    closed = re.search(r'lista fechada[^{}]*\{(\d+(?:\s*,\s*\d+)*)\}',raw)
    explicit = re.search(r'\b(?:somente|apenas|unicamente)\s+(?:n?os?\s+)?(?:compartimentos?\s+)?(\d+(?:\s*(?:,|e)\s*(?:o\s+)?\d+)*)', raw)
    m = typed or explicit or closed
    if not m: return None
    return sorted(int(n) for n in re.findall(r'\d+', m[1]))


def adapt_payload(document, e):
    """Repair non-executable prose payload only with a unique written expression.

    A parseable but altered/truncated model payload is never repaired. That is
    evidence of a binding failure, not permission to replace the assertion.
    """
    receipt = dict(evidence_id=e.evidence_id, original_payload=e.normalized_claim,
                   source_range=[e.source_start,e.source_end], rule='identity', changed=False)
    try:
        representation(e, document)
        return e, receipt
    except ValueError as error:
        receipt['original_rejection'] = str(error)
    from confia_lean_auditor.student_claims.named_math import extract_named_math
    from .registry import PROBLEM_ID
    valid = extract_named_math(PROBLEM_ID, e.subject+': '+e.normalized_claim, VOCABULARY)
    if valid: return e, receipt
    replacement = None
    if e.claim_type == 'integer_set' and _anchor(e, document):
        members = exact_members(e)
        if members: replacement = '{'+','.join(map(str,members))+'}'
    elif e.claim_type == 'math' and _anchor(e, document):
        # Maximal runs preserve every equality side and operator. Two distinct
        # written expressions cannot be silently collapsed to one.
        matches = [m[0].strip() for m in re.finditer(r'[\d(][\d\s()+*/^=.,!\-]*', e.source_span)]
        expressions = [s.rstrip('.,') for s in matches if '=' in s]
        if len(expressions) == 1: replacement = expressions[0]
    if replacement:
        candidate=e.model_copy(update={'normalized_claim':replacement,'metadata':dict(e.metadata,original_payload=e.normalized_claim)})
        try: representation(candidate, document)
        except ValueError: return e, receipt
        receipt.update(changed=True, rule='unique_literal_payload', normalized_payload=replacement)
        return candidate, receipt
    return e, receipt


def literal_property(document,e):
    atom = member_atom(e)
    if atom: return atom
    members = exact_members(e)
    if members is not None:
        return dict(property=e.subject, kind='exact_set', members=members)
    try:
        value=representation(e,document).canonical_form.value
        return dict(property=e.subject,kind=e.claim_type,value=value.get('value',value.get('expression')),
                    expression=value.get('expression'))
    except ValueError:
        if e.subject=='inferiores_brancas' and _anchor(e,document):
            raw=source_view(e.asserted_content)
            numbers=re.findall(r'\b\d+\b',raw)
            if len(numbers)==1:return dict(property=e.subject,kind='math',value=numbers[0])
        # Written color still identifies a replacement even if its withdrawn
        # count is outside the positive checker's grammar.
        if e.subject.startswith('estrategia_') and _anchor(e,document):
            colors={v for k,v in VOCABULARY[e.subject]['values'].items() if re.search(r'\b'+k+r'\b',normalized(e.source_span))}
            if len(colors)==1: return dict(property=e.subject,kind='enum',value=colors.pop())
        if e.subject.startswith('contagem_') and _anchor(e,document):
            m=re.search(r'\b(?:conto|aparece|aparecem)\s+(\d+)\s+(?:posicoes|vezes)',source_view(e.source_span))
            if m:return dict(property=e.subject,kind='math',value=m[1])
    return None


def native_units(document,inventory=None):
    """Translate native framed coordinates to the same original source ledger."""
    with supplement_scope(deterministic_only): digital=collect_tme2_p3_digital(document.items)
    if inventory is not None:
        inventory.extend(r.model_dump(mode='json') for r in digital.records)
    result=[]
    for r in digital.records:
        if r.canonical_form is None:continue  # Unparsed record is audit-only in native inventory.
        if not r.rubric_links: continue
        item=r.rubric_links[0]; value=r.canonical_form.value; subject=r.canonical_form.subject
        if subject not in VOCABULARY:
            # Existing standalone item-a/b probability convention only.
            if item not in 'ab' or r.source.raw_text.strip()!=document.items[item].strip():continue
            subject='primeira_branca' if item=='a' else 'segunda_branca'
        expression=value.get('expression') or (r.source.raw_text if r.source.raw_text.strip()==document.items[item].strip() else None)
        if expression is None: continue
        a=document.ranges[item][0]+r.source.source_start-digital.item_ranges[item][0]
        b=a+len(r.source.raw_text)
        if document.text[a:b]!=r.source.raw_text:raise ValueError('native_coordinate_changed')
        oid=[o for o,s in REGISTRY.items() if subject in s.subjects and o[0]==item]
        if not oid:continue
        result.append(EvidenceUnit(source_evidence_ids=[r.record_id],source_span=r.source.raw_text,
            item_id=item,asserted_content=r.source.raw_text,normalized_claim=expression,subject=subject,
            claim_type=VOCABULARY[subject]['kind'],assertion_status='asserted',polarity='positive',
            scope='main_argument',hypothetical=False,abandoned=False,attributed_to_student=True,
            obligation_candidates=oid,route_candidate='DETERMINISTIC',confidence=0,
            evidence_id='native:'+sha([sha(document.text),a,b,subject,expression])[:24],source_start=a,source_end=b,
            extractor_model='native',metadata=dict(source_sha256=sha(document.text),producer='native',
                native_record_id=r.record_id,native_source_range=[r.source.source_start,r.source.source_end],
                native_role=str(r.semantic_role),native_attribution=r.source.attributable)))
    return tuple(result)
