"""Structured geometry contract supplied in the P4 task, not a Lean geometry proof.

x = PB and P lies on AB, AB = 6, so 0 <= x <= 6. The named equalities,
equilateral triangles and parallelogram are the supplied geometric relations.
Algebraic consequences below are computed from those relations, not a diagram.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class P4Geometry:
    side: int = 6
    source: str = "user:P4-pauta-sections-2-4-7; P on AB, PB=x, AB=6"

    @property
    def lengths(self):
        return {**{s: "x" for s in ("PB", "BQ", "PQ", "AR", "RA")},
                **{s: f"({self.side}-x)" for s in ("AP", "QC", "QR", "RC")}}

    def perimeter(self, polygon):
        segments = {"PBQ": ("PB", "BQ", "PQ"), "RQC": ("QR", "QC", "RC"),
                    "APQR": ("AP", "PQ", "QR", "RA")}[polygon]
        return "+".join(self.lengths[s] for s in segments)

    @property
    def domain(self):
        return f"0 <= x <= {self.side}; from P in segment AB"
