"""Literal structural comparisons; no algebraic correction or semantic oracle."""
import re


TOKEN = re.compile(r"\\[A-Za-z]+|\\.|\d|[A-Za-z]|[^\s]", re.UNICODE)
SCRIPT = re.compile(r"([\^_])\s*(\{[^{}]*\}|\\[A-Za-z]+|\d+|[^\s{}])")


def edit_distance(gold, predicted):
    previous = list(range(len(predicted) + 1))
    for i, a in enumerate(gold, 1):
        current = [i]
        for j, b in enumerate(predicted, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]


def character_error_rate(gold: str, predicted: str):
    edits = edit_distance(gold, predicted)
    # Empty reference: defined 0 for both empty, otherwise undefined rather than an opaque infinity.
    return {"edits": edits, "reference_characters": len(gold),
            "rate": edits / len(gold) if gold else (0.0 if not predicted else None)}


def representation(segment):
    # Preserve both channels; mixed segments must not lose their text or LaTeX.
    return (segment.kind, segment.text, segment.latex)


def math_channels(segment):
    if segment is None:
        return []
    if segment.latex is not None:
        return [segment.latex]
    if segment.kind in {"math", "mixed"} and segment.text is not None:
        return [segment.text]
    return []


def structure(value, marker):
    # Operational handwriting convention: contiguous unbraced digits form one
    # script (x^57 versus x^5 7). This deliberately differs from strict TeX.
    return [(TOKEN.findall(value[:m.start()])[-1:], m.group(2)) for m in SCRIPT.finditer(value) if m.group(1) == marker]


def compare_segments(gold, predicted):
    expected = {(s.page_index, s.order): s for s in gold}
    observed = {(s.page_index, s.order): s for s in predicted}
    if len(expected) != len(gold) or len(observed) != len(predicted):
        raise ValueError("duplicate segment position")
    totals = {"exact_segment_matches": 0, "reference_segments": len(gold), "missing_segments": 0,
              "extra_segments": len(observed.keys() - expected.keys()), "character_edits": 0,
              "reference_characters": 0, "math_symbol_mismatch": 0, "critical_sign_mismatch": 0,
              "exponent_mismatch": 0, "subscript_mismatch": 0}
    details = []
    for key, g in sorted(expected.items()):
        p = observed.get(key)
        exact = p is not None and representation(g) == representation(p)
        totals["exact_segment_matches"] += int(exact)
        totals["missing_segments"] += int(p is None)
        # CER compares channels separately. It includes whitespace and never joins segments.
        cer = [character_error_rate(getattr(g, field) or "", getattr(p, field) or "" if p else "") for field in ("text", "latex")]
        edits = sum(c["edits"] for c in cer)
        chars = sum(c["reference_characters"] for c in cer)
        totals["character_edits"] += edits
        totals["reference_characters"] += chars
        gm, pm = math_channels(g), math_channels(p)
        gt, pt = [TOKEN.findall(v) for v in gm], [TOKEN.findall(v) for v in pm]
        components = {
            "math_symbol_mismatch": int(gt != pt),
            "critical_sign_mismatch": int([t for tokens in gt for t in tokens if t in {"+", "-", "−", "\\pm", "\\mp"}]
                                          != [t for tokens in pt for t in tokens if t in {"+", "-", "−", "\\pm", "\\mp"}]),
            "exponent_mismatch": int([structure(v, "^") for v in gm] != [structure(v, "^") for v in pm]) if any("^" in v for v in gm + pm) else 0,
            "subscript_mismatch": int([structure(v, "_") for v in gm] != [structure(v, "_") for v in pm]) if any("_" in v for v in gm + pm) else 0,
        }
        for name, count in components.items():
            totals[name] += count
        # Operational MMER-v0: union of the disclosed structural components per reference
        # segment, plus missing/extra segments. It is a proxy, not validated mathematical meaning.
        flagged = p is None or any(components.values())
        details.append({"page_index": key[0], "order": key[1], "exact_match": exact,
                        "missing": p is None, "character_edits": edits, "reference_characters": chars,
                        **components, "mmer_flagged": flagged})
    # Extra segments count as insertions in CER.
    for key in observed.keys() - expected.keys():
        p = observed[key]
        totals["character_edits"] += len(p.text or "") + len(p.latex or "")
    reference = totals["reference_characters"]
    flagged = sum(d["mmer_flagged"] for d in details)
    return {**totals,
            "cer": totals["character_edits"] / reference if reference else (0.0 if not totals["character_edits"] else None),
            "exact_segment_match_rate": totals["exact_segment_matches"] / len(gold) if gold else None,
            "mmer_v0": {"definition": "literal-structural-proxy-v0", "scientifically_validated": False,
                        "flagged_reference_segments": flagged, "reference_segments": len(gold),
                        "extra_segments": totals["extra_segments"],
                        "reference_error_rate": flagged / len(gold) if gold else None},
            "segments": details}
