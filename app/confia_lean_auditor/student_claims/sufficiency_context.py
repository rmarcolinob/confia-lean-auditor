"""Deterministic item views of unchanged evidence units, with exact source slices."""
import re
from .evidence_units import evidence_units
from .semantic import normalized
from .evidence_id_semantic import context_restriction


MARKER = re.compile(r'\(([a-d])\)|(?<!\w)([a-d])\)', re.I)
REVISION = re.compile(r'\b(?:descart\w*|rejeit\w*|corrig\w*|retifico|abandonei|releio|errad\w*)\b|na verdade|nao era isso',re.I)


def item_regions(text):
    markers=[]
    for m in MARKER.finditer(text):
        prefix=text[:m.start()];line=prefix.rsplit('\n',1)[-1]
        suffix=text[m.end():].lstrip(' \t')
        if suffix and suffix[0] in '=+*/^<>≤≥−':continue
        # A standalone heading or explicit topical transition; never '+ a)'.
        beginning=not line.strip()
        topical=bool(re.search(r'\b(?:para|em)\s*$',line,re.I))
        sentence_boundary=bool(re.search(r'[.!?;:]\s*$',line))
        if not (beginning or topical or sentence_boundary):continue
        if re.search(r'\b(?:pelo|do|ao|no)?\s*item\s*$',line,re.I):continue
        if m[2] and not (beginning or sentence_boundary):continue
        markers.append((m.start(),(m[1] or m[2]).lower()))
    regions=[]
    if not markers:return [dict(item_id=None,start=0,end=len(text))]
    if markers[0][0]:regions.append(dict(item_id=None,start=0,end=markers[0][0]))
    for i,(start,item) in enumerate(markers):
        regions.append(dict(item_id=item,start=start,end=markers[i+1][0] if i+1<len(markers) else len(text)))
    return regions


def annotated_units(text):
    regions=item_regions(text);result=[]
    for unit in evidence_units(text):
        parts=[]
        for region in regions:
            a=max(region['start'],unit.source_start);b=min(region['end'],unit.source_end)
            if a<b:
                parts.append(dict(item_id=region['item_id'],source_start=a,source_end=b,exact_text=text[a:b]))
        items={p['item_id'] for p in parts}
        result.append(dict(**unit.model_dump(mode='json'),item_id=next(iter(items)) if len(items)==1 else None,
                           multiple_items=len(items)>1,item_slices=parts))
    return result


def meaningful(text):
    return bool(text.strip()) and not re.fullmatch(r'\s*(?:(?:para|em|item)\s*)?\(?[a-d]\)?[).:]?\s*',normalized(text))


def link_evidence(text, requirement, selected_ids):
    units={u['evidence_id']:u for u in annotated_units(text)}
    target=requirement['item_id'];regions=item_regions(text)
    target_context='\n'.join(text[r['start']:r['end']] for r in regions if r['item_id']==target)
    explicit=set(re.findall(r'\b(?:item|parte)\s*\(?([a-d])\)?\b',normalized(target_context)))
    if re.search(r'\bitem anterior\b',normalized(target_context)) and target in 'bcd':explicit.add(chr(ord(target)-1))
    declared=set(requirement['authorized_source_items'])
    allowed=declared|explicit|{target}
    bindings=[];exceptions=[];rejected=[];unassigned=False
    for identifier in selected_ids:
        if identifier not in units:
            rejected.append(dict(evidence_id=identifier,reason='unknown_evidence_id'));continue
        unit=units[identifier];parts=[]
        for part in unit['item_slices']:
            item=part['item_id']
            # Mixed units are narrowed to the authorized item. An unlabelled
            # preamble within such a unit is context, not positive evidence.
            if item is None and unit['multiple_items']:continue
            if item is None:
                unassigned=True;parts.append(part)
            elif item in allowed:
                parts.append(part)
                if item!=target:
                    exceptions.append(dict(evidence_id=identifier,source_item=item,target_item=target,
                        authorization='explicit_textual_reference' if item in explicit else 'declared_cross_item_obligation'))
        if not parts:
            rejected.append(dict(evidence_id=identifier,reason='wrong_item'));continue
        bindings.append(dict(evidence_id=identifier,original_unit=unit,authorized_slices=parts,
            context_only=not any(meaningful(p['exact_text']) for p in parts)))
    if bindings and all(b['context_only'] for b in bindings):
        rejected.extend(dict(evidence_id=b['evidence_id'],reason='header_only') for b in bindings)
    valid=bool(bindings) and not rejected and len(set(selected_ids))==len(selected_ids)
    # Context can veto or disambiguate, never supply missing positive evidence.
    relevant_items={p['item_id'] for b in bindings for p in b['authorized_slices']}
    local_context='\n'.join(text[r['start']:r['end']] for r in regions if r['item_id'] in relevant_items)
    last=max((p['source_end'] for b in bindings for p in b['authorized_slices']),default=0)
    later=[]
    for unit in units.values():
        if unit['source_end']>last and REVISION.search(normalized(unit['exact_text'])):
            later.append(dict(evidence_id=unit['evidence_id'],exact_text=unit['exact_text']))
    return dict(valid=valid,target_item=target,bindings=bindings,exceptions=exceptions,rejected=rejected,
        unassigned_item=unassigned,local_context=local_context,later_revisions=later,
        reason='valid_unlabelled_pending_sufficiency' if valid and unassigned else 'valid' if valid else 'invalid_item_linkage')


def context_gate(linkage, judgment):
    if not linkage['valid']:return dict(valid=False,reason=linkage['reason'])
    if judgment.assertion_mode!='asserted':return dict(valid=False,reason='nonasserted_context')
    scope=linkage['local_context']+'\n'+'\n'.join(r['exact_text'] for r in linkage['later_revisions'])
    stub=type('Selection',(),{'mathematical_payload':type('Payload',(),{'subject':judgment.obligation_id.split('.',1)[1]})()})()
    reason=context_restriction(scope,stub)
    if reason:return dict(valid=False,reason=reason)
    if re.search(r'na pagina\s+\d|ignore.*instru|desconsidere.*instru',normalized(scope)):
        return dict(valid=False,reason='instruction_or_document_context')
    return dict(valid=True,reason='asserted_with_global_revision_check')
