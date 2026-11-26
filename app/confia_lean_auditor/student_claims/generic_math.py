"""Bounded source-span detection. Parsing is owned by core.math_canonical.

No problem assets, expected answers, checkers or network are used here. A
candidate records an assertion, including a false or unsupported assertion.
"""
from dataclasses import replace
import hashlib
import re

from confia_lean_auditor.core.math_canonical import parse_math
from confia_lean_auditor.core.math_canonical.normalization import mathematical_dash_at
from confia_lean_auditor.core.math_canonical.parser import FUNCTIONS, GREEK_NAMES, ALIASES
from confia_lean_auditor.student_claims.grounding import (
    normalized, local_integer_bindings, representation_matches, _digest, _payload,
)
from confia_lean_auditor.student_claims.schemas import StudentClaim

VERSION = 'generic-source-v1'
MAX_SOURCE = 20000
MAX_CANDIDATES = 256
MAX_FRAGMENT = 2048
WORDS = dict(zip('zero um uma dois duas três tres quatro cinco seis sete oito nove dez onze doze treze catorze quatorze quinze dezesseis dezessete dezoito dezenove vinte'.split(),
                 [0,1,1,2,2,3,3,4,5,6,7,8,9,10,11,12,13,14,14,15,16,17,18,19,20]))
NUMBER = r'(?:[+-]?\d+(?:[.,]\d+)?|(?:menos\s+)?(?:' + '|'.join(WORDS) + r'))\b'
BINDING = re.compile(r'(?<![\w+*/^=<>−-])([A-Za-z])\s*(?:vale\b|(?:é|e)\s+igual\s+a\b|igual\s+a\b|é\b)\s*(' + NUMBER + r')(?![\w+*/^=<>]|[.,]\d)', re.I)
VALUE = re.compile(r'\b(?P<label>(?:(?:primeiro|último|ultimo)\s+algarismo|algarismo\s+inicial|algarismo|resposta|resto|valor(?:\s+pedido|\s+final)?|termo\s+independente))'
    r'(?P<subject>\s+(?:de|do)\s+[^.!?\n]{1,100}?)?(?:,\s*da\s+esquerda\s+para\s+a\s+direita,)?\s*'
    r'(?P<neg>não\s+|nao\s+)?(?:é\b|e\b|vale\b|=|:)\s*', re.I)
PROPERTY = re.compile(r'(?<!\w)([A-Za-z])\s+(?:(não|nao)\s+)?(?:é\s+|e\s+)?(injetiva|injetora|ímpar|impar|par)\b', re.I)
SEQUENCE = re.compile(r'\b(?:a\s+)?sequência\s+é\s+(?:uma\s+)?PG\b|\b(?:a\s+)?sequencia\s+e\s+(?:uma\s+)?PG\b', re.I)
CONCLUSION = re.compile(r'\b(?:logo|portanto|assim|dai|conclu\w*|obtemos|resulta|segue\s+que|resposta|algarismo|valor\s+(?:e|pedido))\b')
REJECTED = re.compile(r'\b(?:tentamos|tentei|tentativa|abandon\w*|descart\w*|rejeit\w*|impossivel|absurdo|falh\w*|isso\s+daria)\b')
ASSUMPTION = re.compile(r'\b(?:suponh\w*|hipotese|talvez|acho)\b')
TOKEN = re.compile(r'\\[A-Za-z]+|\d+(?:[.,]\d+)?|[^\W\d]\w*|<=|>=|!=|=>|[+*/^=<>≠≤≥−·×±(){}\[\],.;:$\n-]|\S', re.UNICODE)
MATH_WORDS = FUNCTIONS | GREEK_NAMES | set(ALIASES) | {'log','log_10','sqrt','arg','binom','choose'}
RELATION = re.compile(r'(?<![<>=!])=(?!=|>)|[<>≤≥≠]|!=')


def _literal(word):
    value = normalized(word).strip()
    negative = value.startswith('menos ')
    if negative:
        value = value[6:]
    return str((-1 if negative else 1) * WORDS[value]) if value in WORDS else word


def _complete_word_number(source, end):
    """A small verbal vocabulary must never accept a compound-number prefix."""
    tail=source[end:]
    if re.match(r'\s*[.,]\d',tail):
        return False
    if not tail.strip() or re.match(r'\s*[,.;!?\n]',tail):
        return True
    return bool(re.match(r'\s+e\s+[A-Za-z]\s*(?:=|vale\b|é\b|igual\s+a\b)',tail,re.I))


def _math_word(token):
    return (token in MATH_WORDS or bool(re.fullmatch(r'[A-Za-zα-ωΑ-Ω](?:_?\d+|[₀-₉⁰¹²³⁴⁵⁶⁷⁸⁹]+)?', token))
            or bool(re.fullmatch(r'\\[A-Za-z]+', token)))


def math_runs(text):
    """Locate maximal token runs, without interpreting their mathematics.

    Prose and clause boundaries terminate runs. Invalid tails remain attached;
    we never recover a shorter, apparently valid expression from a bad RHS.
    """
    start = end = None
    depth = 0
    for match in TOKEN.finditer(text):
        token = match[0]
        separator = token in {';', ':', '\n', '.', '=>'} or (token == ',' and depth == 0)
        allowed = (_math_word(token) or token[0].isdigit()
                   or bool(re.fullmatch(r'[+*/^=<>≠≤≥−·×±(){}\[\],$-]|<=|>=|!=', token))
                   or (token == '–' and mathematical_dash_at(text, match.start())))
        # Unknown adjacent identifiers belong to the same unsupported fragment,
        # never to a discarded suffix of an apparently valid numeric value.
        if start is not None and match.start()==end and re.fullmatch(r'\w+',token):
            allowed = True
        # "e" between two explicit assignments is a clause conjunction.
        if token.lower() == 'e' and start is not None and RELATION.search(text[start:match.start()]) and re.match(r'\s+[A-Za-z]\s*(?:=|vale|é)', text[match.end():]):
            separator = True
        if separator or not allowed:
            if start is not None:
                yield start, end, text[start:end]
            start = end = None
            depth = 0
            continue
        if start is None:
            start = match.start()
        end = match.end()
        depth += token in {'(', '[', '{'}
        depth -= token in {')', ']', '}'}
    if start is not None:
        yield start, end, text[start:end]


def _mathematical_data(fragment, *, allow_value=False):
    parsed = parse_math(fragment)
    if parsed.status == 'invalid':
        return None
    relation = bool(RELATION.search(fragment))
    interval = fragment.startswith('[') and fragment.endswith((']', ')'))
    expression = bool(re.search(r'[+*/^²³−·×]|\\frac|\b(?:sin|sen|cos|log)', fragment))
    if not (relation or interval or expression or allow_value):
        return None
    if not relation and not interval and parsed.status != 'parsed' and not expression:
        return None
    kind = 'math_relation' if relation else 'math_interval' if interval else 'math_expression'
    return kind, {'expression': fragment}


def candidate_spans(source):
    """Yield literal spans plus lossless, typed source interpretations."""
    if len(source) > MAX_SOURCE:
        return
    candidates = []
    covered = []
    def add(a, b, kind, data):
        if 0 <= a < b <= len(source) and b-a <= MAX_FRAGMENT:
            candidates.append((a, b, kind, data))
    for match in BINDING.finditer(source):
        if re.search(r'[A-Za-zÀ-ÿ]',match[2]) and not _complete_word_number(source,match.end()):
            continue
        expression = match[1] + '=' + _literal(match[2])
        if parse_math(expression).status == 'parsed':
            add(match.start(), match.end(), 'math_relation', {'expression': expression})
            covered.append((match.start(), match.end()))
    for match in VALUE.finditer(source):
        suffix = source[match.end():]
        literal = re.match(NUMBER, suffix, re.I)
        run = next(math_runs(suffix), None)
        if literal and (run is None or run[0] != 0):
            if re.search(r'[A-Za-zÀ-ÿ]',literal[0]) and not _complete_word_number(suffix,literal.end()):
                continue
            end, expression = literal.end(), _literal(literal[0])
        elif run and run[0] == 0:
            end, expression = run[1], run[2]
        else:
            continue
        data = _mathematical_data(expression, allow_value=True)
        if data is None:
            continue
        label = normalized(match['label'])
        concept = ('leading_digit' if label in {'primeiro algarismo','algarismo inicial'} else
                   'last_digit' if label == 'ultimo algarismo' else 'digit' if label == 'algarismo' else
                   'remainder' if label == 'resto' else 'answer' if label == 'resposta' else 'value')
        payload = {'expression': expression, 'concept': concept, 'negated': bool(match['neg'])}
        if match['subject']:
            payload['subject_text'] = match['subject'].strip()
        add(match.start(), match.end()+end, 'math_value', payload)
        covered.append((match.start(), match.end()+end))
    for match in PROPERTY.finditer(source):
        prop = normalized(match[3])
        add(match.start(), match.end(), 'math_property', {'subject':match[1],
            'property':'injective' if prop.startswith('injet') else 'odd' if prop=='impar' else 'even',
            'negated':bool(match[2])})
        covered.append((match.start(), match.end()))
    for match in SEQUENCE.finditer(source):
        add(match.start(), match.end(), 'math_property', {'subject':'sequence','property':'geometric_progression','negated':False})
        covered.append((match.start(), match.end()))
    for a,b,fragment in math_runs(source):
        if any(a >= x and b <= y for x,y in covered):
            continue
        relations = list(RELATION.finditer(fragment))
        # Keep each adjacent equality in a chain; never infer endpoints.
        if len(relations)>1 and all(m[0]=='=' for m in relations) and len(relations)<=16:
            cuts=[0]+[m.end() for m in relations]
            ends=[m.start() for m in relations]+[len(fragment)]
            for i in range(len(relations)):
                left,right=cuts[i],ends[i+1]
                raw=fragment[left:right];trim=len(raw)-len(raw.lstrip());raw=raw.strip()
                value=_mathematical_data(raw)
                if value:add(a+left+trim,a+left+trim+len(raw),*value)
        else:
            value=_mathematical_data(fragment)
            if value:add(a,b,*value)
    # Complete integer bindings in ONE local clause, reusing the P0 binder.
    for clause in re.finditer(r'[^\n;.!?]+(?:\.(?=\d)[^\n;.!?]*)*', source):
        members=[c for c in candidates if c[0]>=clause.start() and c[1]<=clause.end() and c[2]=='math_relation']
        bindings=[]
        for a,b,_,data in members:
            m=re.fullmatch(r'([A-Za-z])\s*=\s*([+-]?\d+)',data['expression'])
            if m:bindings.append((a,b,m[1],int(m[2])))
        if len({c[2] for c in bindings})>1:
            a,b=min(c[0] for c in bindings),max(c[1] for c in bindings)
            symbols=tuple(sorted({c[2] for c in bindings}))
            values=local_integer_bindings('; '.join(f'{c[2]}={c[3]}' for c in bindings),symbols)
            if values is not None:
                add(a,b,'math_bindings',{'bindings':values})
                candidates=[c for c in candidates if not (c[2]=='math_relation' and c[0]>=a and c[1]<=b and any(c[0]==x[0] and c[1]==x[1] for x in bindings))]
    seen=set()
    for candidate in sorted(candidates,key=lambda c:(c[0],c[1],c[2])):
        key=_digest(candidate)
        if key not in seen:
            seen.add(key)
            yield candidate
            if len(seen)>=MAX_CANDIDATES:
                return


def extract_generic_math(problem_id, source):
    digest=hashlib.sha256(source.encode()).hexdigest()
    claims=[]
    for a,b,kind,data in candidate_spans(source):
        claim=StudentClaim(id=f'generic_math_{a}_{b}_{kind[5:]}',problem_id=problem_id,
            claim_type=kind,raw_text=source[a:b],normalized_text=data.get('expression',source[a:b]),
            context=source[max(0,a-100):min(len(source),b+100)],data=data,method='generic_math',confidence=1.0)
        claim.grounding={'status':'grounded','validator':VERSION,'extraction_method':'generic_math',
            'source_text':source[a:b],'source_start':a,'source_end':b,'source_sha256':digest,
            'payload_sha256':_digest(_payload(claim)),
            'reason':'Literal mathematical candidate; detection is not verification'}
        claims.append(claim)
    return claims


def source_is_valid(payload, source):
    """Reconstruct syntax from the saved literal span, never trust annotations."""
    g=payload.get('grounding') or {}
    a,b=g.get('source_start'),g.get('source_end')
    if (g.get('validator')!=VERSION or g.get('extraction_method')!='generic_math'
            or type(a)!=int or type(b)!=int or not 0<=a<b<=len(source)
            or source[a:b]!=g.get('source_text') or payload.get('raw_text')!=source[a:b]
            or g.get('source_sha256')!=hashlib.sha256(source.encode()).hexdigest()
            or g.get('payload_sha256')!=_digest(_payload(payload))):
        return False
    return any(x==0 and y==b-a and kind==payload['claim_type'] and data==payload['data']
               for x,y,kind,data in candidate_spans(source[a:b]))


def contextual_role(source, a, b, statement=''):
    from confia_lean_auditor.rubric.positive_evidence import source_contexts, attributable, Rule, quoted_ranges
    from confia_lean_auditor.claims.common.schemas import SemanticRole
    if any(a<y and b>x for x,y in quoted_ranges(source)):
        return SemanticRole.QUOTED_STATEMENT, False
    contexts=[(x,y,text) for x,y,text in source_contexts(source) if x<=a and y>=b]
    allowed=[c for c in contexts if attributable(c[2],Rule(()),statement)
             and not REJECTED.search(normalized(c[2])) and not ASSUMPTION.search(normalized(c[2]))]
    if not allowed:
        text=normalized(' '.join(c[2] for c in contexts))
        if REJECTED.search(text):return SemanticRole.REJECTED_ATTEMPT,False
        if ASSUMPTION.search(text):return SemanticRole.ASSUMPTION,False
        if re.search(r'\b(?:enunciado|citacao|citado)\b',text):return SemanticRole.QUOTED_STATEMENT,False
        return SemanticRole.UNKNOWN,False
    x,_,_=min(allowed,key=lambda c:len(c[2]))
    text=source[x:b]
    return (SemanticRole.CONCLUSION if CONCLUSION.search(normalized(text)) else SemanticRole.INTERMEDIATE),True


def merge_candidates(specific, generic, source):
    """Deduplicate only equivalent content at overlapping literal source spans.

    Retain the existing ID/payload, and record both extraction origins. Unknown
    or conflicting interpretations remain separate candidates.
    """
    from confia_lean_auditor.claims.common.adapters import claim_from_student
    from confia_lean_auditor.claims.common.canonical import mathematical_value
    from confia_lean_auditor.core.math_canonical import compare_canonical
    from confia_lean_auditor.core.math_canonical.models import canonical_from_dict
    merged=list(specific);retained=[]
    old_records=[claim_from_student(c,solution_text=source) for c in specific]
    for candidate in generic:
        record=claim_from_student(candidate,solution_text=source)
        found=False
        for i,legacy in enumerate(merged):
            old=old_records[i]
            if not record.source.attributable or not old.source.attributable:
                continue
            if not (old.source.source_start<=record.source.source_start and old.source.source_end>=record.source.source_end):
                continue
            left,right=mathematical_value(old.canonical_form),mathematical_value(record.canonical_form)
            equal=bool(left and right and compare_canonical(canonical_from_dict(left),canonical_from_dict(right)).status=='equivalent')
            if candidate.claim_type=='math_bindings' and old.canonical_form and old.canonical_form.family=='integer_bindings':
                equal=old.canonical_form.value==candidate.data['bindings']
            if not equal:
                # Existing source-to-payload validators may recognize the same
                # complete statement even when canonical families differ.
                equal=representation_matches(legacy.claim_type,legacy.data,candidate.raw_text)
            if equal:
                g=dict(legacy.grounding)
                origins=list(g.get('extraction_origins',[g.get('extraction_method')]))
                if 'generic_math' not in origins:origins.append('generic_math')
                g['extraction_origins']=origins
                g['generic_source_ids']=list(dict.fromkeys(g.get('generic_source_ids',[])+[candidate.id]))
                merged[i]=replace(legacy,grounding=g);found=True;break
        if not found:retained.append(candidate)
    combined=merged+retained
    # Report competing literal assignments without silently selecting a winner.
    # A pair of alternatives may be intentional, so this is ambiguity, not a
    # mathematical refutation. Non-attributable hypotheses do not poison facts.
    bindings={}
    for index,claim in enumerate(combined):
        record=claim_from_student(claim,solution_text=source)
        if not record.source.attributable:continue
        values=claim.data.get('bindings') if claim.claim_type=='math_bindings' else None
        if record.canonical_form and record.canonical_form.family=='integer_bindings':
            values=record.canonical_form.value
        if claim.claim_type=='math_relation':
            m=re.fullmatch(r'([A-Za-z])\s*=\s*([+-]?\d+)',claim.data['expression'])
            if m:values={m[1]:int(m[2])}
        for symbol,value in (values or {}).items():
            bindings.setdefault(symbol,[]).append((index,value))
    conflicts={i for values in bindings.values() if len({v for _,v in values})>1 for i,_ in values}
    for i in conflicts:
        combined[i]=replace(combined[i],grounding={**combined[i].grounding,
            'interpretation_status':'ambiguous','interpretation_reason':'Competing grounded assignments retained; no automatic selection'})
    return combined
