"""Serializable syntax and outcomes, with no proof or grading authority."""
from dataclasses import asdict, dataclass
import json
from typing import Optional


@dataclass(frozen=True)
class MathNode:
    kind: str
    value: Optional[str] = None
    args: tuple = ()


@dataclass(frozen=True)
class CanonicalMath:
    kind: str
    tree: MathNode
    affine: Optional[tuple] = None
    relation: Optional[str] = None
    variables: tuple = ()
    schema_version: str = 'canonical-math-v1'
    domain: str = 'real_total'

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))


@dataclass(frozen=True)
class ParseResult:
    status: str
    reason: str
    canonical_form: Optional[CanonicalMath] = None


@dataclass(frozen=True)
class EquivalenceResult:
    status: str
    reason: str
    basis: Optional[str] = None


def canonical_from_dict(data):
    """Read a validated local canonical payload; never execute its contents."""
    def node(value, depth=0):
        if depth>32 or set(value)-{'kind','value','args'}:
            raise ValueError('Invalid canonical tree')
        return MathNode(value['kind'],value.get('value'),tuple(node(n,depth+1) for n in value.get('args',())))
    if data.get('schema_version')!='canonical-math-v1' or data.get('domain')!='real_total':
        raise ValueError('Unsupported canonical schema/domain')
    return CanonicalMath(kind=data['kind'],tree=node(data['tree']),
        affine=None if data.get('affine') is None else tuple(tuple(t) for t in data['affine']),
        relation=data.get('relation'),variables=tuple(data.get('variables',())))
