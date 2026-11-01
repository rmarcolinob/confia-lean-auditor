"""P2 diagram reasoning, independently of any handwriting recognition.

The four fixed labelled lines are A-center-E, B-center-F, C-center-G, D-center-H.
No arrangement is compared to a model picture. Recognition must supply a
confirmed structured transcription; this module does not inspect image pixels.
"""
import hashlib
import json
from typing import Literal, Optional

from pydantic import BaseModel,ConfigDict,Field,StrictBool,StrictInt,StrictStr,model_validator

from confia_lean_auditor.claims.common.schemas import (
    CanonicalForm,MathClaimRecord,Origin,Provenance,SemanticRole,StructuredSourceBinding,
)

LINES=(('A','E'),('B','F'),('C','G'),('D','H'))
POSITIONS=frozenset('ABCDEFGH')


class TME2P2DiagramState(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    center: Optional[StrictInt]=None
    positions: dict[str,Optional[StrictInt]]=Field(default_factory=dict)

    @model_validator(mode='after')
    def labelled_positions(self):
        if not set(self.positions)<=POSITIONS:raise ValueError('Unknown P2 position')
        if any(abs(n)>10**6 for n in [self.center,*self.positions.values()] if n is not None):
            raise ValueError('Diagram integer out of bounds')
        return self


class DiagramProvenance(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    source_ref: StrictStr=Field(min_length=1,max_length=500)
    image_ref: Optional[StrictStr]=None
    page_index: Optional[int]=Field(default=None,ge=0)
    regions: dict[str,tuple[float,float,float,float]]=Field(default_factory=dict)
    confidence: Optional[float]=Field(default=None,ge=0,le=1,allow_inf_nan=False)
    position_confidence: dict[str,float]=Field(default_factory=dict)
    confirmed: StrictBool=False
    origin: Literal['student','reference','unknown']='student'


class DiagramSubmission(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    state: TME2P2DiagramState
    source: DiagramProvenance


def inspect_diagram(state,*,required_center=None):
    state=TME2P2DiagramState.model_validate(state.model_dump() if isinstance(state,TME2P2DiagramState) else state)
    values=[state.center,*[state.positions.get(k) for k in sorted(POSITIONS)]]
    complete=all(v is not None for v in values)
    known=[v for v in values if v is not None]
    pairs=[(state.positions.get(a),state.positions.get(b)) for a,b in LINES]
    sums=[a+state.center+b if a is not None and b is not None and state.center is not None else None for a,b in pairs]
    exact=complete and sorted(known)==list(range(1,10))
    balanced=complete and len(set(sums))==1
    center_ok=required_center is None or state.center==required_center
    return dict(complete=complete,used_values=known,duplicates=len(set(known))!=len(known),
        uses_1_to_9_exactly_once=exact,opposite_pairs=pairs,line_sums=sums,
        all_four_lines_balanced=balanced,required_center=required_center,center_correct=center_ok,
        common_line_sum=sums[0] if balanced else None,valid=exact and balanced and center_ok)


def feasible_pairs(center,common_sum):
    remaining=set(range(1,10))-{center};pairs=[]
    while remaining:
        a=min(remaining);b=common_sum-center-a
        if b==a or b not in remaining:return None
        pairs.append((a,b));remaining-={a,b}
    return tuple(pairs)


def admissible_cases():
    return tuple((x,(45+3*x)//4) for x in range(1,10) if (45+3*x)%4==0)


def diagram_record(submission,item,document_digest,index):
    submitted=DiagramSubmission.model_validate(submission.model_dump() if isinstance(submission,DiagramSubmission) else submission)
    payload=submitted.state.model_dump(mode='json')
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    source=submitted.source.model_dump()
    attributable=source['confirmed'] and source['origin']=='student'
    binding=StructuredSourceBinding(kind='diagram_structured',**source,payload=payload,payload_sha256=digest,
        source_sha256=document_digest,grounding_status='grounded' if source['confirmed'] else 'unresolved',attributable=attributable)
    identifier=hashlib.sha256(json.dumps([item,index,source,payload],sort_keys=True).encode()).hexdigest()[:24]
    return MathClaimRecord(record_id='diagram:'+identifier,problem_id='TME2026P2',claim_type='diagram_state',
        provenance=Provenance(origin=Origin.REFERENCE_EXPECTED if source['origin']=='reference' else
            Origin.STUDENT_EXPLICIT if attributable else Origin.STUDENT_CANDIDATE,
            channel='native',extraction_method='diagram_structured.v1'),source=binding,
        canonical_form=CanonicalForm(family='diagram_state',subject='four_opposite_lines',value=payload,method='diagram_structured.v1'),
        canonicalization_status='parsed',canonicalization_reason='Explicit structured positions; no image recognition performed',
        semantic_role=SemanticRole.CONCLUSION,rubric_links=(item,))


def recognize_p2_diagram_from_image(*args,**kwargs):
    """Explicit upstream interface; existing HMER has no A-H topology contract."""
    raise NotImplementedError('Arbitrary handwriting-to-P2 DiagramState recognition is not implemented; supply reviewed structured evidence')
