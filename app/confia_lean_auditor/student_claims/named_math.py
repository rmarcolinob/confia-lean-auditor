"""Opt-in typed mathematical notation: declared quantity: value.

The vocabulary comes from a problem contract. This is a line grammar, not a
prose classifier: unknown labels, unsupported values and ellipses fail closed.
Uses existing MathClaimRecord, bounded canonicalization and contextual grounding.
"""
import hashlib
import re
import ast

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


def extract_named_math(problem_id, source, vocabulary, *, introductions=None):
    if len(source) > 20000:
        return ()
    digest = hashlib.sha256(source.encode()).hexdigest()
    records = []
    for line in re.finditer(r"[^\n]+", source):
        raw = line[0].strip()
        if len(raw) > 2048:
            continue
        if ":" in raw:
            label, value = raw.split(":", 1)
            key = label_key(label)
        else:
            matches = [(key, re.fullmatch(re.escape(phrase)+r"\s+(.+)", raw, re.IGNORECASE))
                       for phrase, key in (introductions or {}).items()]
            matches = [(key, match[1]) for key, match in matches if match]
            if len(matches) != 1:
                continue
            key, value = matches[0]
            value = value.removesuffix('.')
        if key not in vocabulary or "..." in value or "…" in value:
            continue
        value = value.strip()
        spec = vocabulary[key]
        data = {"quantity": key, "expression": value, "value_kind": spec["kind"]}
        mathematical_form = None
        if spec["kind"] == "combinatorial_math":
            from confia_lean_auditor.core.math_canonical.combinatorial import factorial_form
            form = factorial_form(value)
            if form is None:
                continue
            data["structure"] = form
        elif spec["kind"] == "integer_pairs":
            if '#' in value:
                continue
            parsed = literal_form(value)
            if not parsed or parsed[0] != "math_finite_collection":
                continue
            members = parsed[1].value
            if members["subject"] is not None or any(not isinstance(p, list) for p in members["elements"]):
                continue
            data["structure"] = members["elements"]
        elif spec["kind"] == "integer_mapping":
            if '#' in value:
                continue
            try:
                node = ast.parse(value, mode='eval').body
                if not isinstance(node, ast.Dict) or not 1 <= len(node.keys) <= 32:
                    continue
                mapping = {}
                for k, v in zip(node.keys, node.values):
                    key_name = k.id if isinstance(k, ast.Name) else k.value if isinstance(k, ast.Constant) else None
                    if (not isinstance(key_name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,30}', key_name)
                            or key_name in mapping or not isinstance(v, ast.Constant) or type(v.value) is not int or abs(v.value)>10**6):
                        raise ValueError('Invalid explicit integer mapping')
                    mapping[key_name] = v.value
                data["structure"] = mapping
            except (ValueError, SyntaxError, RecursionError, AttributeError):
                continue
        elif spec["kind"] == "congruence":
            match = re.fullmatch(r'(.+?)\s*(?:≡|congruent)\s*(.+?)\s*\(\s*mod\s+(\d+)\s*\)', value)
            if not match or not 1 <= int(match[3]) <= 1000:
                continue
            forms = [parse_math(t) for t in (match[1], match[2])]
            if any(p.status != 'parsed' or p.canonical_form.kind != 'expression' for p in forms):
                continue
            data["structure"] = dict(left=match[1], right=match[2], modulus=int(match[3]),
                                     forms=[p.canonical_form.to_dict() for p in forms])
        elif spec["kind"] in {"positive_multiset", "partition_table", "factored_product"}:
            from confia_lean_auditor.core.math_canonical.integer_structures import (
                positive_multiset, partition_table, product_form,
            )
            parser = {"positive_multiset": positive_multiset, "partition_table": partition_table,
                      "factored_product": product_form}[spec["kind"]]
            structured = parser(value)
            if structured is None:
                continue
            data["structure"] = structured
        elif spec["kind"] == "math":
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
        elif spec["kind"] in {"expression_set", "set_equality"}:
            groups = value.split("=")
            if len(groups) != (2 if spec["kind"] == "set_equality" else 1):
                continue
            sets = []
            for group in groups:
                group = group.strip()
                if not (group.startswith("{") and group.endswith("}")):
                    break
                members = [p.strip() for p in group[1:-1].split(",")]
                parsed = [parse_math(p) for p in members]
                if not 1 <= len(members) <= 12 or any(p.status != "parsed" or
                        p.canonical_form.kind != "expression" for p in parsed):
                    break
                sets.append({"expressions": members, "forms": [p.canonical_form.to_dict() for p in parsed]})
            if len(sets) != len(groups):
                continue
            data["sets"] = sets
        elif spec["kind"] == "relation":
            parsed = parse_math(value)
            if parsed.status != "parsed" or parsed.canonical_form.kind not in {"equality", "inequality"}:
                continue
            mathematical_form = parsed.canonical_form.to_dict()
            data["relation"] = mathematical_form
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
