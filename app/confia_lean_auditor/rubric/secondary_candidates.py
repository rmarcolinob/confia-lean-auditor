"""Bounded, literal source spans for secondary adjudication, never new claims."""
import copy
import re
import unicodedata

MAX_CANDIDATES = 8
MAX_SPAN = 800
MAX_CRITERION_TEXT = 2400
STOP = set('para como uma com dos das que por pelo pela corretamente criterio pauta apresenta obtem obtém conclui mostra demonstra'.split())


def _terms(text):
    plain = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(c))
    return {w[:6] for w in re.findall(r'[a-z]{3,}', plain) if w not in STOP}


def _local_spans(source):
    """Paragraphs and sentences/lines keep context; no sliding-window fragments."""
    for match in re.finditer(r'\S[\s\S]*?(?=\n[ \t]*\n|\Z)', source):
        start, end = match.span()
        while end > start and source[end - 1].isspace(): end -= 1
        if end - start <= MAX_SPAN:
            yield start, end
        # Line/sentence alternatives also let us omit a sensitive neighboring span.
        for part in re.finditer(r'[^\n]+?(?:[.!?](?=\s|$)|(?=\n|$))', source[start:end]):
            a, b = start + part.start(), start + part.end()
            while a < b and source[a].isspace(): a += 1
            while b > a and source[b-1].isspace(): b -= 1
            if 0 < b-a <= MAX_SPAN: yield a, b


def candidate_binding(candidate, source):
    a, b = candidate.get('source_start'), candidate.get('source_end')
    return (type(a) is int and type(b) is int and 0 <= a < b <= len(source)
            and candidate.get('source_text') == source[a:b]
            and bool(source[a:b].strip()) and b-a <= MAX_SPAN
            and candidate.get('grounding_status') == 'grounded')


def build_candidates(source, criterion, *, prefix, redact):
    selected, seen = [], set()
    def add(a, b, kind, **metadata):
        candidate = {'source_start': a, 'source_end': b, 'source_text': source[a:b] if type(a) is int and type(b) is int else None,
                     'source_kind': kind, 'grounding_status': 'grounded', **metadata}
        if not candidate_binding(candidate, source) or (a,b) in seen: return
        if redact(candidate['source_text']) != candidate['source_text']: return
        if len(selected) >= MAX_CANDIDATES or sum(len(x['source_text']) for x in selected)+b-a > MAX_CRITERION_TEXT: return
        seen.add((a,b)); candidate['evidence_id'] = f'{prefix}_{len(selected)+1}'
        selected.append(candidate)
    # Context already filtered these checks through source_matches and relevance.
    for check in criterion.get('candidate_student_checks', []):
        g = check.get('grounding') or {}
        a,b=g.get('source_start'),g.get('source_end')
        if type(a) is int and type(b) is int and g.get('status') == 'grounded' and g.get('source_text') == source[a:b]:
            add(g.get('source_start'),g.get('source_end'),'grounded_claim',
                claim_id=check.get('id'),verification_status=check.get('status','not_checked'))
    for claim in criterion.get('grounded_claims', []):
        span=claim.get('source_span') or {};a,b=span.get('start'),span.get('end')
        if type(a) is int and type(b) is int and claim.get('text') == source[a:b]:
            add(a,b,'math_claim_record',math_claim_record_id=claim.get('math_claim_record_id'),
                semantic_role=claim.get('semantic_role'),verification_status=claim.get('verification') or 'not_checked')
    for text in criterion.get('existing_evidence', []):
        if isinstance(text,str) and text and text in source:
            a=source.find(text);add(a,a+len(text),'criterion_evidence',verification_status='not_checked')
    query=' '.join([criterion.get('description',''),criterion.get('id','').replace('_',' '),
                    *[r.get('description','') for r in criterion.get('coded_requirements',[])]])
    terms=_terms(query)
    ranked=[]
    for a,b in set(_local_spans(source)):
        rank=len(terms & _terms(source[a:b]))
        ranked.append((-rank,a,b))
    ranked.sort()
    for negative_rank,a,b in ranked:
        if negative_rank==0: continue
        # Prefer context-bearing paragraphs over redundant nested sentences.
        if any(x['source_kind']=='local_context' and x['source_start']<=a and b<=x['source_end'] for x in selected): continue
        add(a,b,'local_context',verification_status='not_checked')
    if not selected:
        # One actual short context for terse replies (including "não sei").
        for _,a,b in ranked:
            add(a,b,'bounded_context',verification_status='not_checked')
            if selected: break
    return selected


def with_candidates(payload, redact):
    result=copy.deepcopy(payload)
    for index,c in enumerate(result['pending_criteria'],1):
        if 'candidate_evidence' not in c:
            c['candidate_evidence']=build_candidates(result['solution_text'],c,prefix=f'E{index}',redact=redact)
    return result


def wire_candidates(candidates):
    fields={'evidence_id','source_text','source_start','source_end','source_kind','grounding_status','verification_status','semantic_role'}
    return [{k:v for k,v in c.items() if k in fields} for c in candidates]
