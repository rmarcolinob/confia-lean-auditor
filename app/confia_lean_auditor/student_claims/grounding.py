"""Conservative source binding, independent of mathematical truth.

Offsets always index the original Python string (Unicode code points). Local
re-extraction proposes candidates; representation validation must also succeed.
Unknown grammar, rejected hypotheses and conflicting candidates fail closed.
"""
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
import re
import unicodedata

VERSION = "local-source-v1"
FINAL = re.compile(r"\b(?:portanto|logo|resposta|conclu\w*|assim)\b", re.I)
REJECTED = re.compile(r"\b(?:nao|nunca|falha\w*|errad\w*|descart\w*|tentei|tentativa|hipotese|suponha|talvez|se)\b")


def normalized(text):
    # No offsets are taken from this representation.
    text = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: "^" + unicodedata.normalize("NFKC", m[0]), text)
    text = text.lower().replace("−", "-").replace("–", "-").replace("·", "*").replace("≡", "=")
    text = text.replace("α", "alpha").replace("β", "beta").replace("√", "sqrt")
    text = re.sub(r"\bsen\b", "sin", text)
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def compact(text):
    return re.sub(r"\s+", "", normalized(text))


def contexts(source):
    """Original sentence/paragraph boundaries; keep negation with its clause."""
    boundaries = {0, len(source)}
    for m in re.finditer(r"(?:[.!?](?=\s|$)|\n\s*\n)", source):
        boundaries.add(m.end())
    ordered = sorted(boundaries)
    for a, b in zip(ordered, ordered[1:]):
        while a < b and source[a].isspace(): a += 1
        while b > a and source[b-1].isspace(): b -= 1
        if a < b:
            yield a, b, source[a:b]


def _binding_values(text, symbols):
    t = normalized(text)
    found = {symbol: [] for symbol in symbols}
    for m in re.finditer(r"(?<!\w)([a-z])\s*(?:=|vale\b|e\s+igual\s+a\b)\s*([+-]?\d+)", t):
        symbol, number = m[1], m[2]
        if symbol not in found:
            continue
        prefix, suffix = t[:m.start()].rstrip(), t[m.end():].lstrip()
        if prefix and prefix[-1] in "+-*/^=<>\\": continue
        if suffix and (suffix[0] in "+-*/^=<>" or re.match(r"[.,]\d|\d|[a-df-z_(]", suffix)): continue
        if suffix.startswith("e") and not re.match(r"e\b", suffix): continue
        found[symbol].append(int(number))
    return found


def local_integer_bindings(text, symbols):
    """Complete local literal assignments, never prefixes or inferred values."""
    found = _binding_values(text, symbols)
    if any(len(set(values)) != 1 for values in found.values()):
        return None
    return {symbol: values[0] for symbol, values in found.items()}


def binding_candidates(source, symbols):
    return [(a,b,text,data) for a,b,text in contexts(source)
            if not REJECTED.search(normalized(text))
            and (data := local_integer_bindings(text, symbols)) is not None]


def select_bindings(source, symbols):
    candidates = binding_candidates(source, symbols)
    final = [c for c in candidates if FINAL.search(c[2])]
    pool = final or candidates
    conflicts = [text for _,_,text in contexts(source)
                 if not REJECTED.search(normalized(text))
                 and any(len(set(v)) > 1 for v in _binding_values(text, symbols).values())]
    if conflicts and (not final or any(FINAL.search(text) for text in conflicts)):
        return None, "ambiguous", "Conflicting assignments inside a local clause"
    if not pool:
        return None, "unresolved", "No complete local binding for the requested symbols"
    if len({json.dumps(c[3],sort_keys=True) for c in pool}) != 1:
        return None, "ambiguous", "Conflicting local bindings without a unique conclusion"
    return pool[-1], "grounded", "Complete local assignments; explicit conclusion preferred"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _field(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def _payload(claim):
    return {k:_field(claim,k) for k in ("problem_id", "claim_type", "data")}


def _math_fragment(text, expression):
    """Require a complete math fragment, never a prefix such as k in k+1."""
    t, expr = normalized(text), compact(expression)
    pattern = r"(?<![\w+*/^=-])" + r"\s*".join(re.escape(ch) for ch in expr)
    for match in re.finditer(pattern, t):
        prefix=t[:match.start()].rstrip()
        if prefix and prefix[-1] in "+*/^=-":
            continue
        tail=t[match.end():].lstrip()
        if tail and (tail[0] in "+*/^=<>-([" or re.match(r"[.,]\d|\d", tail)):
            continue
        if match.end()<len(t) and re.match(r"[a-z_]",t[match.end()]):
            continue
        return True
    return False


def _scaled(value):
    result = Fraction(value.replace(",", ".")) * 10000
    return int(result) if result.denominator == 1 else None


def _equality_chain(source, lhs, rhs):
    """Match explicitly written equality chains; never infer the omitted RHS."""
    if _math_fragment(source, lhs + "=" + rhs):
        return True
    t = normalized(source)
    start = r"(?<![\w+*/^=-])" + r"\s*".join(re.escape(ch) for ch in compact(lhs)) + r"\s*="
    for match in re.finditer(start, t):
        chain = re.split(r"[,;]|\.(?!\d)", t[match.end():], maxsplit=1)[0]
        parts = chain.split("=")
        # Intermediate expressions must consist solely of math tokens. This is
        # syntactic correspondence, not a proof that those equalities are true.
        if len(parts) > 1 and all(re.fullmatch(r"(?:[\s\d.+*/^()\-]|x|a|b|sin|cos|alpha|beta|sqrt|log)+", p) for p in parts[:-1]):
            if compact(parts[-1]) == compact(rhs):
                return True
    return False


def representation_matches(kind, data, source):
    """Independent correspondence checks; these do NOT decide correctness.

    Adapters cover existing claim grammars. Unrecognized representations stay
    unresolved instead of gaining trust merely by reproducing an extractor.
    """
    t, c = normalized(source), compact(source)
    try:
        if kind == "f2q1_student_final_answer":
            return local_integer_bindings(source, ("a", "b")) == data
        if kind == "arithmetic_equality":
            return _math_fragment(source, data["left_expr"] + "=" + data["right_expr"])
        if kind == "f2q1_student_power_reduction":
            from confia_lean_auditor.student_claims.extract_f2q1_student_claims import PAIR_BY_EXPR
            pair = PAIR_BY_EXPR.get(data["rhs"])
            return pair == (data["const"],data["coeff"]) and _equality_chain(source, f'x^{data["exponent"]}', data["rhs"])
        if kind == "f2q1_student_reduced_form":
            forms = {"correct":"(a+b)x-a", "wrong_const_sign":"(a+b)x+a", "wrong_coeff_minus":"(a-b)x-a", "wrong_coeff_swapped_minus":"(b-a)x-a"}
            formula = data["formula_text"].replace("*", "")
            return formula == forms.get(data["form_kind"]) and _math_fragment(source.replace("*", ""), formula)
        if kind == "f2q1_student_coefficient_system":
            lhs = {"candidateA + candidateB":"a+b", "candidateB + candidateA":"b+a"}.get(data["sum_lhs"])
            a = {"neg_a":"-a", "a":"a"}.get(data["a_equation_kind"])
            return bool(lhs and a and _math_fragment(source, f'{lhs}={data["sum_rhs"]}') and _math_fragment(source, f'{a}={data["a_rhs"]}'))
        if kind == "f2q5_student_log_power_decomposition":
            # The value must end the SAME logarithm equality chain, not another
            # equation elsewhere in the clause mentioning a logarithm.
            decimal_source = re.sub(r"(?<=\d),(?=\d)", ".", t)
            values = [_scaled(m[1]) for m in re.finditer(r"=\s*(\d+\.\d+)(?![\d+*/^=-]|[.,]\d)", decimal_source)
                      if any(_equality_chain(decimal_source, lhs, m[1])
                             for lhs in ("log10(3^100)", "log(3^100)"))]
            total = data["total_log_scaled"]
            integer = (total // 10000) * 10000
            return total in values and data["integer_part_scaled"] == integer and data["mantissa_scaled"] == total-integer
        if kind == "f2q5_student_mantissa":
            return any(_scaled(m[1]) == data["mantissa_scaled"] for m in re.finditer(r"mantissa\s*(?:e|=|vale)?\s*(\d+[.,]\d+)(?![\d+*/^=-]|[.,]\d)",t))
        if kind == "f2q5_student_digit_log_bounds":
            values = {int(m[1]):_scaled(m[2]) for m in re.finditer(r"log(?:10)?\s*\(?\s*([56])\s*\)?\s*=\s*(\d+[.,]\d+)(?![\d+*/^=-]|[.,]\d)",t)}
            return values.get(5)==data["log5_scaled"] and values.get(6)==data["log6_scaled"]
        if kind == "f2q5_student_between_bounds":
            return any(tuple(_scaled(v) for v in m.groups()) == tuple(data[k] for k in ("left_scaled","middle_scaled","right_scaled")) for m in re.finditer(r"(?<![\d.,])(\d+[.,]\d+)\s*<\s*(\d+[.,]\d+)\s*<\s*(\d+[.,]\d+)(?![\d+*/^=-]|[.,]\d)",t))
        if kind == "f2q5_student_final_digit":
            # This validates only claims already extracted; it does not add new digit detection.
            return any(int(m[1])==data["digit"] for m in re.finditer(r"(?:primeiro\s+algarismo|algarismo\s+inicial|resposta)(?:\s+(?:de|do)\s+(?:resultado\s+de\s+)?3\^?100)?\s*(?:e|=)\s*(\d+)(?![\d+*/^=-]|[.,]\d)",t))
        if kind == "f2q6_student_final_answer":
            values = [int(m[1]) for m in re.finditer(r"(?<![\w+*/^=-])n\s*=\s*(\d+)(?![\d+*/^=-]|[.,]\d)", t)]
            return bool(values) and sorted(set(values))==data["values"]
        if kind == "f2q6_student_probability_formula":
            formulas = {"correct":["c(n-1,3)/2^n","c(n-1;3)/2^n","binom(n-1,3)/2^n","choose(n-1,3)/2^n"],"wrong_choose_n_3":["c(n,3)/2^n","c(n;3)/2^n"],"correct_numerator_wrong_denominator_n_minus_1":["c(n-1,3)/2^(n-1)","c(n-1;3)/2^(n-1)"]}
            # Formula occurs as a full RHS, so prefix '=' is allowed intentionally.
            return any(_math_fragment(source.replace("=", ":"), f) for f in formulas.get(data["formula_kind"],[]))
        if kind == "f2q6_student_ratio_formula":
            formulas={"correct":["n/(2n-6)","n/[2n-6]","n/(2(n-3))","n/[2(n-3)]"],"wrong_n_minus_1_over_2n":["(n-1)/(2n)"],"wrong_n_minus_1_over_2n_minus_6":["(n-1)/(2n-6)"],"wrong_n_over_2n":["n/(2n)"],"wrong_n_over_2n_minus_8":["n/(2n-8)"]}
            return any(_math_fragment(source.replace("=", ":"), f) for f in formulas.get(data["ratio_kind"],[]))
        if kind == "f2q3_student_beta_difference":
            from confia_lean_auditor.core.audit_math_projection import has_equivalent_equality
            return has_equivalent_equality(source, f'cos(beta)-sin(beta)={data["value_expr"]}')
        if kind.startswith("f2q3_student_"):
            expr = data["expr"].replace("sqrt7", "sqrt(7)")
            if kind == "f2q3_student_candidate_value":
                names = {"sin_beta":"sinBetaCandidate", "cos_beta":"cosBetaCandidate", "sin_alpha":"sinAlphaCandidate", "cos_alpha":"cosAlphaCandidate"}
                if names.get(data["value_name"]) != data["lean_lhs"]: return False
                lhs = data["value_name"].replace("_", "")
                return _equality_chain(source, lhs, expr)
            if kind == "f2q3_student_final_sin_sum":
                return _equality_chain(source, "sin(alpha+beta)", expr)
            if kind == "f2q3_student_final_answer":
                return _equality_chain(source, "sin(alpha+beta)", expr) or bool(FINAL.search(source) and _math_fragment(source.replace("=",":"), expr))
        if kind.startswith("f2q8_student_"):
            if kind == "f2q8_student_final_answer":
                return any(int(m[1])==data["student_value"] for m in re.finditer(r"(?:resposta|resultado|valor(?:\s+pedido|\s+final)?|soma)\s*(?:e|=|:|vale|igual\s+a)?\s*(-?\d+)(?![\d+*/^=-]|[.,]\d)", t))
            if kind == "f2q8_student_pair_count":
                return bool(re.search(r"(?<!\d)"+str(data["pair_count"])+r"\s+pares?\b",t))
            if kind == "f2q8_student_pair_reduction":
                expr=f'2025-{data["subtracted_pair_count"]}'
                if "stated_value" in data: expr += "="+str(data["stated_value"])
                return bool(re.search(r"par|agrup|soma|alternad",t)) and _math_fragment(source, expr)
            if kind == "f2q8_student_alternating_sum_value":
                return _math_fragment(source.replace("…","..."), "1-2+3-4+...+2025="+str(data["student_value"]))
            if kind == "f2q8_student_det_formula":
                forms={"minus_one_pow_k_minus_1_times_k":"(-1)^(k-1)k", "minus_one_pow_k_times_k":"(-1)^kk", "minus_one_pow_k_minus_1_times_k_plus_1":"(-1)^(k-1)(k+1)","positive_k":"k","negative_k":"-k"}
                f=compact(data["formula_text"]).replace("*", "")
                if f != forms.get(data["formula_kind"]): return False
                return _math_fragment(source.replace("*", "").replace("=", ":"), f)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False
    return False


def _key(claim):
    data = _field(claim,"data",{})
    return (_field(claim,"claim_type"), data.get("exponent"), data.get("value_name"))


def _meaning(data):
    return {k:v for k,v in data.items() if k not in {"formula_text", "ratio_text"}}


def ground_student_claims(source, claims, extractor):
    """Use original local clauses; no synthetic raw_text is trusted as source."""
    local = []
    for a,b,text in contexts(source):
        if len(text)>1200 or REJECTED.search(normalized(text)): continue
        for candidate in extractor(text, _ground=False):
            if representation_matches(candidate.claim_type,candidate.data,text):
                local.append((a,b,text,candidate))
    result=[]
    for claim in claims:
        candidates=[c for c in local if _key(c[3])==_key(claim)]
        if "final" in claim.claim_type:
            finals=[c for c in candidates if FINAL.search(c[2])]
            candidates=finals or candidates
        signatures={_digest(_meaning(c[3].data)) for c in candidates}
        matching=[c for c in candidates if _meaning(c[3].data)==_meaning(claim.data)
                  and representation_matches(claim.claim_type,claim.data,c[2])]
        status = "ambiguous" if len(signatures)>1 else "grounded" if matching else "unresolved"
        reason = {"ambiguous":"Conflicting local representations; no unique attribution", "grounded":"Local re-extraction and independent representation validation agree", "unresolved":"No local source representation consistent with all structured values"}[status]
        if claim.grounding and claim.grounding.get("status")=="ambiguous":
            status,reason="ambiguous",claim.grounding["reason"]
        grounding={"status":status,"reason":reason,"extraction_method":extractor.__name__,"validator":VERSION,"source_sha256":hashlib.sha256(source.encode()).hexdigest()}
        if matching and status=="grounded":
            a,b,text,_=matching[-1]
            grounding.update(source_text=text,source_start=a,source_end=b,payload_sha256=_digest(_payload(claim)))
        result.append(replace(claim,grounding=grounding))
    return result


def has_valid_grounding(claim):
    g=_field(claim,"grounding")
    if not isinstance(g,dict) or g.get("status")!="grounded" or g.get("validator")!=VERSION: return False
    text=g.get("source_text"); start=g.get("source_start"); end=g.get("source_end")
    if not isinstance(text,str) or not text or type(start)!=int or type(end)!=int or start<0 or end-start!=len(text): return False
    method, digest = g.get("extraction_method"), g.get("source_sha256")
    if not isinstance(method, str) or not method or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest): return False
    try:
        return (g.get("payload_sha256")==_digest(_payload(claim)) and not REJECTED.search(normalized(text))
                and representation_matches(_field(claim,"claim_type"),_field(claim,"data"),text))
    except (TypeError, ValueError):
        return False


def source_matches(claim, solution):
    g=_field(claim,"grounding",{}) or {}
    return (has_valid_grounding(claim) and g["source_sha256"]==hashlib.sha256(solution.encode()).hexdigest()
            and solution[g["source_start"]:g["source_end"]]==g["source_text"])
