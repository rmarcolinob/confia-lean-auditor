from __future__ import annotations
"""Source coordinates and temporal locality, independent of mathematical truth."""
from dataclasses import dataclass, asdict
import re
from confia_lean_auditor.student_claims.semantic import sha, normalized

VERSION = 'p3-segments-v1'
# A dot is a decimal separator only between digits. Fractions may end sentences.
BOUNDARY = re.compile(r'\n|[!?]|(?<!\d)\.|\.(?!\d)')

@dataclass(frozen=True)
class DiscourseSegment:
    segment_id: str
    item_id: str
    subject: str
    envelope_range: tuple
    clause_range: tuple
    assertion_range: tuple
    paragraph_id: int
    block_id: str
    ordinal: int
    previous: str | None
    next: str | None
    episode_id: str
    acts: tuple
    source_sha256: str
    coordinate_system: str = 'unicode_codepoint_half_open'
    topic_change: bool = False
    scope: str = 'assertion'
    speaker: str = 'student_or_unresolved'

    def as_dict(self):
        return asdict(self)

@dataclass(frozen=True)
class ClaimEpisode:
    episode_id: str
    item_id: str
    subject: str
    segment_ids: tuple
    relation_refs: tuple

    def as_dict(self):
        return asdict(self)


def segments(document, views):
    """Aliases share a temporal segment; envelopes never determine ordering."""
    groups = {}
    for e in views:
        a, b = e.metadata.get('assertion_range', (e.source_start, e.source_end))
        key = (e.item_id, a, b, e.subject)
        groups.setdefault(key, []).append(e)
    ordered = sorted(groups, key=lambda k: (k[1], k[2], k[0], k[3]))
    ids = {k: 'segment:' + sha([VERSION, sha(document.text), k]) for k in ordered}
    result = {}
    for n, k in enumerate(ordered):
        e = groups[k][0]; raw = normalized(document.text[k[1]:k[2]])
        paragraph = len(re.findall(r'\n\s*\n', document.text[:k[1]]))
        episode = 'episode:' + sha([sha(document.text), e.item_id, paragraph, e.subject])
        acts = tuple(name for name, pattern in (
            ('correction', r'corrig|substitu|retific|invalido|retiro|na verdade'),
            ('hypothesis', r'hipotese|suponh|supondo'), ('attempt', r'tentativa'),
            ('conclusion', r'conclu|definitiv|resultado|resposta'),
            ('quotation', r'citacao|disse|dizia|transcrevo'),
        ) if re.search(pattern, raw)) or ('assertion',)
        seg = DiscourseSegment(ids[k], e.item_id, e.subject,
            tuple(e.metadata.get('envelope_range', (e.source_start,e.source_end))),
            (e.source_start,e.source_end), (k[1],k[2]), paragraph,
            f'{e.item_id}:{paragraph}', n, ids[ordered[n-1]] if n else None,
            ids[ordered[n+1]] if n+1<len(ordered) else None, episode, acts, sha(document.text),topic_change=bool(n and ordered[n-1][0::3]!=k[0::3]),
            scope='quoted' if 'quotation' in acts else 'hypothesis' if 'hypothesis' in acts else 'assertion',
            speaker='third_party_or_unresolved' if 'quotation' in acts else 'student_or_unresolved')
        for alias in groups[k]: result[alias.evidence_id] = seg.as_dict()
    return result
