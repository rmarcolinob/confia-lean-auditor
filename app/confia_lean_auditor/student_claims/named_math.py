"""Opt-in typed mathematical notation: declared quantity: value.

The vocabulary comes from a problem contract. This is a line grammar, not a
prose classifier: unknown labels, unsupported values and ellipses fail closed.
Uses existing MathClaimRecord, bounded canonicalization and contextual grounding.
"""
import hashlib
import re

from confia_lean_auditor.claims.common.schemas import (
    CanonicalForm, MathClaimRecord, Origin, Provenance, SourceBinding,
)
from confia_lean_auditor.core.math_canonical import parse_math
from .digital_literals import literal_form
from .generic_math import contextual_role
from .grounding import normalized

VERSION = "digital-quantity.v1"


def label_key(text):
    return "_".join(normalized(text).strip().split()).lower()


def extract_named_math(problem_id, source, vocabulary):
    if len(source) > 20000:
        return ()
    digest = hashlib.sha256(source.encode()).hexdigest()
    records = []
    for line in re.finditer(r"[^\n]+", source):
        raw = line[0].strip()
        if len(raw) > 2048 or ":" not in raw:
            continue
        label, value = raw.split(":", 1)
        key = label_key(label)
        if key not in vocabulary or "..." in value or "…" in value:
            continue
        value = value.strip()
        spec = vocabulary[key]
        data = {"quantity": key, "expression": value, "value_kind": spec["kind"]}
        mathematical_form = None
        if spec["kind"] == "math":
            parsed = [parse_math(p.strip()) for p in value.split("=")]
            if not parsed or any(p.status != "parsed" or p.canonical_form.kind != "expression" for p in parsed):
                continue
            data["parts"] = [p.canonical_form.to_dict() for p in parsed]
            mathematical_form = parse_math(value).canonical_form
            mathematical_form = mathematical_form.to_dict() if mathematical_form else None
        elif spec["kind"] == "enum":
            member = label_key(value)
            if member not in spec["values"]:
                continue
            data["value"] = spec["values"][member]
        elif spec["kind"] == "integer_set":
            parsed = literal_form(value)
            if not parsed or parsed[0] != "math_finite_collection":
                continue
            collection = parsed[1].value
            if collection["subject"] is not None or any(type(x) is not int for x in collection["elements"]):
                continue
            data["value"] = collection["elements"]
        else:
            raise ValueError("Unsupported declared quantity type")
        start = line.start() + len(line[0]) - len(line[0].lstrip())
        end = start + len(raw)
        role, attributable = contextual_role(source, start, end, "")
        records.append(MathClaimRecord(record_id=f"native:{VERSION}:{start}:{end}",
            problem_id=problem_id, claim_type="math_named_quantity",
            provenance=Provenance(origin=Origin.STUDENT_EXPLICIT if attributable else Origin.STUDENT_CANDIDATE,
                channel="native", extraction_method=VERSION),
            source=SourceBinding(grounding_status="grounded", raw_text=raw, source_start=start,
                source_end=end, source_sha256=digest, attributable=attributable),
            semantic_role=role, canonical_form=CanonicalForm(family="named_quantity", subject=key,
                value=data, method=VERSION, mathematical_form=mathematical_form),
            canonicalization_status="parsed", canonicalization_reason="Explicit typed notation; no truth inferred"))
    return tuple(records)
