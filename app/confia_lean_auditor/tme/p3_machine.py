"""Six-compartment P3 machine: immutable bottom-first stacks, two draws only."""
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from itertools import product

COLORS = frozenset({"white", "black", "gray"})


@dataclass(frozen=True)
class P3Machine:
    stacks: tuple[tuple[str, ...], ...]
    source_reference: str

    def __post_init__(self):
        if (len(self.stacks) != 6 or any(len(s) < 2 for s in self.stacks)
                or any(c not in COLORS for s in self.stacks for c in s)
                or not self.source_reference):
            raise ValueError("P3 requires six sourced stacks with at least two known colors each")

    @property
    def bottom_colors(self):
        return tuple(s[0] for s in self.stacks)

    def after_first(self, compartment):
        if type(compartment) is not int or not 1 <= compartment <= 6:
            raise ValueError("Compartments are numbered 1 to 6")
        return tuple(s[1] if i == compartment else s[0] for i, s in enumerate(self.stacks, 1))

    def counts_after_first(self, compartment):
        return Counter(self.after_first(compartment))

    def second_white_pairs(self):
        return frozenset((i, j) for i, j in self.ordered_pairs()
                         if self.after_first(i)[j-1] == "white")

    def ordered_pairs(self):
        return frozenset(product(range(1, len(self.stacks) + 1), repeat=2))

    def continue_compartments(self):
        return frozenset(i for i, color in enumerate(self.bottom_colors, 1) if color == "white")

    def best_choices(self, compartment):
        counts = self.counts_after_first(compartment)
        best = max(counts.values())
        return frozenset(c for c, n in counts.items() if n == best), best

    def second_white_branches(self):
        return tuple(Fraction(self.counts_after_first(i)["white"], 6) for i in range(1, 7))

    def win_probability(self):
        return sum((Fraction(1, 6) * Fraction(self.best_choices(i)[1], 6)
                    for i in self.continue_compartments()), Fraction(0))


def load_machine(path):
    import json
    from pathlib import Path
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return P3Machine(tuple(tuple(s) for s in data["stacks_bottom_first"]), data["source_reference"])
