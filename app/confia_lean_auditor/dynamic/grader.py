"""Source-grounded exact DY3 grading. Unsupported semantics stay review-only.

The executable criterion language is intentionally closed: an extra condition in
an approved criterion cannot be silently dropped by a keyword match. No LLM score,
problem ID, Specialized checker, model confidence or reference answer is authority.
"""

import json
import hashlib
import subprocess
import re
import unicodedata
from decimal import Decimal, ROUND_DOWN
from fractions import Fraction
from math import isqrt
from pathlib import Path
from datetime import datetime, timezone
from .verification import polynomial, add, VERSION
from .substitution import substitution_operation
from .method_sufficiency import method_coverage, is_factorization, is_restatement, PARTIAL_METHOD_SUFFIX
from .versions import GRADER_VERSION, EXTRACTOR_VERSION, NORMALIZATION_VERSION, SUFFICIENCY_VERSION
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.core.paths import get_repo_root
from .grading_models import (
    StudentClaim,
    RubricBinding,
    DynamicRubricDecision,
    DynamicStudentSolutionAnalysis,
    DynamicAuditResult,
)


def plain(text):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


def norm(text):
    text = (
        text.replace("²", "^2")
        .replace("³", "^3")
        .replace("−", "-")
        .replace("×", "*")
        .replace("·", "*")
        .replace("√", "sqrt")
    )
    text = re.sub(r"\s+", "", text).rstrip(".")
    text = re.sub(r"(?<=\d)(?=[a-zA-Z(])", "*", text)
    return re.sub(r"(?<=\))(?=[a-zA-Z(\d])", "*", text)


def shape(text):
    return re.sub(r"\(([-+]?\d+(?:/\d+)?)\)", r"\1", norm(text))


def exact(text):
    def sqrt(m):
        x = Fraction(m[1])
        n, d = isqrt(x.numerator), isqrt(x.denominator)
        if n * n != x.numerator or d * d != x.denominator:
            raise ValueError("irrational root")
        return str(Fraction(n, d))

    p = polynomial(re.sub(r"sqrt\((\d+(?:/\d+)?)\)", sqrt, norm(text)), "@")
    return p.get(0, Fraction(0))


def proportional(a, b):
    if not a or not b or set(a) != set(b):
        return False
    k = next(iter(b))
    ratio = a[k] / b[k]
    return bool(ratio) and all(a[i] == ratio * b[i] for i in a)


def problem_equation(statement):
    if not re.search(r"\breai?s\b|\bR\b|ℝ", statement, re.I):
        raise ValueError("real domain not explicit")
    # Do not drop additional restrictions or obligations surrounding the equation.
    if not re.fullmatch(
        r"\s*Resolva\s+(?:no conjunto dos reais|nos reais|em R|em ℝ)\s*:\s*[\dA-Za-z²³+\-−*/^(). \t]+=[\d+\-*/(). \t]+[.]?\s*",
        statement,
        re.I,
    ):
        raise ValueError("additional or unsupported statement conditions")
    found = []
    for left, right in re.findall(
        r"([\dA-Za-z²³+\-−*/^(). \t]+)=([\d+\-*/(). \t]+)", statement
    ):
        letters = re.findall(r"[a-zA-Z]", left)
        if len(set(letters)) != 1:
            continue
        var = letters[0]
        p = add(polynomial(norm(left), var), polynomial(norm(right), var), -1)
        if max(p, default=0) in {1, 2}:
            found.append((left.strip(), right.strip(), var, p))
    if len(found) != 1:
        raise ValueError("unsupported or ambiguous equation")
    left, right, var, p = found[0]
    a, b, c = p.get(2, Fraction(0)), p.get(1, Fraction(0)), p.get(0, Fraction(0))
    if not a:
        roots = {-c / b}
    else:
        disc = b * b - 4 * a * c
        if disc < 0:
            raise ValueError("no real roots")
        n, d = isqrt(disc.numerator), isqrt(disc.denominator)
        if n * n != disc.numerator or d * d != disc.denominator:
            raise ValueError("irrational roots")
        roots = {(-b + Fraction(n, d)) / (2 * a), (-b - Fraction(n, d)) / (2 * a)}
    return left, right, var, p, roots


def criterion_policy(criterion):
    if criterion.notes.strip() or criterion.teacher_guidance.strip():
        return None, False
    text = " ".join(plain(criterion.description).strip().rstrip(".").split())
    method_partial = text.endswith(PARTIAL_METHOD_SUFFIX)
    if method_partial:
        text = text[:-len(PARTIAL_METHOD_SUFFIX)].rstrip(".")
    suffix = " credito parcial proporcional as raizes corretas"
    partial = text.endswith(suffix)
    if partial:
        text = text[: -len(suffix)].rstrip(".")
    policy = {
        "obter todas as raizes reais": "roots",
        "obter a solucao real": "roots",
        "obter as raizes corretas": "roots",
        "justificar a resolucao por transformacoes equivalentes": "method",
        "justificar a fatoracao": "factorization",
        "simplificar a equacao por uma transformacao equivalente": "transformation",
        "verificar as raizes por substituicao": "substitution",
    }.get(text)
    if method_partial:
        return (policy, True) if policy == "method" and not partial else (None, False)
    return (
        (None, False)
        if partial and policy not in {"roots", "substitution"}
        else (policy, partial)
    )


def extract(solution, equation, checker=None):
    claims = []
    warnings = []
    left, right, var, p, roots = equation
    for match in re.finditer(r"[^;\n]+", solution):
        raw = match[0]
        text = raw.strip()
        if not text:
            continue
        start = match.start() + len(raw) - len(raw.lstrip())
        s = norm(text)
        adoption = "ADOPTED"
        if re.match(r"(?i)(descarto|abandono|riscado)\s*:", text):
            adoption = "ABANDONED"
            s = norm(text.split(":", 1)[1])
        elif re.search(r"\b(se|suponha|talvez|hipotese)\b", plain(text)):
            adoption = "HYPOTHETICAL"
        elif re.search(r"\b(nao|incerto)\b|\?", plain(text)):
            adoption = "AMBIGUOUS"
        claim = StudentClaim(
            schema_version="student-claim.r1",
            claim_id=f"claim_{len(claims)+1}",
            start=start,
            end=start + len(text),
            text=text,
            normalized=s,
            claim_type="UNSUPPORTED",
            subject=var,
            fidelity="UNSUPPORTED",
            adoption=adoption,
            verification_status="REVIEW_ONLY",
            verification_detail="Representação não coberta pela gramática; nenhum argumento foi inventado.",
        )
        try:
            answer = re.fullmatch(r"(?:S|" + re.escape(var) + r")=\{([^{}]+)\}", s)
            single = re.fullmatch(re.escape(var) + r"=([-+]?\d+(?:/\d+)?)", s)
            operation = substitution_operation(text, equation, norm, exact)
            if operation:
                claim.claim_type = "SUBSTITUTION"
                claim.substitution = operation
                claim.values = [operation["substituted_value"]] if operation["verifies_root"] else []
                valid = operation["evaluation_verified"]
            elif answer or single:
                values = [
                    exact(v) for v in (answer[1].split(",") if answer else [single[1]])
                ]
                valid = (
                    bool(values)
                    and len(values) == len(set(values))
                    and (set(values) == roots if answer else set(values) <= roots)
                )
                claim.verified_values = [str(v) for v in values if v in roots]
                claim.components = [
                    {
                        "kind": "root_membership",
                        "value": str(v),
                        "status": "VERIFIED" if v in roots else "REFUTED",
                    }
                    for v in values
                ]
                claim.claim_type = "ROOTS" if answer else "ROOT"
                claim.values = list(map(str, values))
            elif "=" in s:
                parts = s.split("=")
                if parts[0] == var and len(parts) in {2, 3} and "sqrt(" in parts[1]:
                    a, b, c = p.get(2, 0), p.get(1, 0), p.get(0, 0)
                    disc = b * b - 4 * a * c
                    allowed = (
                        {
                            shape(f"({-b}{sign}sqrt({disc}))/({2*a})")
                            for sign in ["+", "-"]
                        }
                        if a
                        else set()
                    )
                    if shape(parts[1]) not in allowed:
                        raise ValueError("ungrounded formula")
                    value = exact(parts[1])
                    valid = value in roots and (
                        len(parts) == 2 or exact(parts[2]) == value
                    )
                    claim.claim_type = "FORMULA"
                    claim.values = [str(value)]
                    claim.strategy_context = "quadratic_formula"
                elif len(parts) == 2 and var in s:
                    a1, a2 = polynomial(parts[0], var), polynomial(parts[1], var)
                    delta = add(a1, a2, -1)
                    valid = proportional(delta, p) or (
                        not delta and proportional(a1, p)
                    )
                    if parts[0] == parts[1]:
                        raise ValueError("restated identity is not development")
                    claim.claim_type = "TRANSFORMATION"
                    claim.strategy_context = (
                        "factorization" if is_factorization(s, var) else "equivalent_transformations"
                    )
                    if is_restatement(s, norm(left + "=" + right), var):
                        claim.claim_type = "RESTATEMENT"
                else:
                    parts = (
                        parts[1:]
                        if re.fullmatch(r"D|Delta|delta|Δ", parts[0])
                        else parts
                    )
                    if len(parts) < 2:
                        raise ValueError("missing equation")
                    valid = all(exact(x) == exact(parts[0]) for x in parts)
                    claim.claim_type = "ARITHMETIC"
            else:
                raise ValueError("unsupported")
            claim.verification_status = "VERIFIED" if valid else "REFUTED"
            claim.fidelity = "FAITHFUL" if s == text else "SUPPORTED_NORMALIZATION"
            claim.verification_detail = (
                "Checagem exata e vínculo com a equação original; sem certificado Lean."
            )
            claim.components.append(
                {
                    "kind": "claim",
                    "status": claim.verification_status,
                    "verifier": VERSION,
                }
            )
            if claim.verification_status == "VERIFIED":
                claim.verified_values = list(claim.values)
            if checker:
                try:
                    claim = checker(claim)
                except Exception:
                    claim.verification_status = "ERROR"
                    claim.verification_detail = "Falha do verificador; não é refutação."
                    claim.verified_values = []
                    claim.components = [
                        {"kind": "claim", "status": "ERROR", "verifier": VERSION}
                    ]
        except (ValueError, ZeroDivisionError, OverflowError, RecursionError):
            pass
        except Exception:
            claim.verification_status = "ERROR"
            claim.verification_detail = "Falha do verificador; não é refutação."
            claim.verified_values = []
            claim.components = [
                {"kind": "claim", "status": "ERROR", "verifier": VERSION}
            ]
        if (
            claim.fidelity == "UNSUPPORTED"
            or adoption in {"AMBIGUOUS", "HYPOTHETICAL"}
            or claim.verification_status == "ERROR"
        ):
            warnings.append(
                f"{claim.claim_id}: interpretação ou verificação requer revisão."
            )
        if adoption == "AMBIGUOUS":
            claim.fidelity = "AMBIGUOUS"
            claim.polarity = (
                "NEGATIVE" if re.search(r"\bnao\b", plain(text)) else "UNKNOWN"
            )
        if adoption == "HYPOTHETICAL":
            claim.polarity = "UNKNOWN"
        claims.append(claim)
    return claims, warnings


class DynamicSolutionGrader:
    def __init__(self, checker=None):
        self.checker = checker

    def grade(self, source, statement, rubric, preparation, context, artifact_dir):
        if context.grader_version != GRADER_VERSION:
            raise ValueError("Historical grader context cannot execute under a different engine version.")
        equation = None
        try:
            equation = problem_equation(statement.statement)
            claims, warnings = extract(source.solution_text, equation, self.checker)
        except (ValueError, ZeroDivisionError, OverflowError):
            claims = []
            warnings = ["Enunciado fora do escopo exato; revisão docente necessária."]
        active = [
            c
            for c in claims
            if c.adoption == "ADOPTED"
            and c.fidelity in {"FAITHFUL", "SUPPORTED_NORMALIZATION"}
        ]
        roots = equation[-1] if equation else set()
        answers = [c for c in active if c.claim_type in {"ROOTS", "ROOT", "FORMULA"}]
        sets = {tuple(sorted(c.values)) for c in answers if c.claim_type == "ROOTS"}
        conflict = len(sets) > 1 or (
            any(c.verification_status == "REFUTED" for c in answers)
            and any(c.verification_status == "VERIFIED" for c in answers)
        )
        methods = {
            c.strategy_context
            for c in active
            if c.claim_type in {"TRANSFORMATION", "FORMULA"}
            and c.verification_status == "VERIFIED"
        }
        if len(methods) > 1:
            methods.discard("equivalent_transformations")
        strategy = (
            next(iter(methods))
            if len(methods) == 1
            else "mixed" if methods else "unknown"
        )
        known = (
            " ".join(
                [
                    plain(s.strategy_label)
                    for s in preparation.proposal.candidate_reference_solutions
                ]
                + [
                    plain(s.description)
                    for s in preparation.proposal.alternative_strategies
                ]
            )
            if preparation.proposal
            else ""
        )
        known_match = (strategy == "factorization" and "fatora" in known) or (
            strategy == "quadratic_formula"
            and ("quadratica" in known or "bhaskara" in known)
        )
        strategy_status = (
            "KNOWN_STRATEGY"
            if known_match
            else "VALID_ALTERNATIVE_CANDIDATE" if methods else "UNKNOWN_STRATEGY"
        )
        if len(methods) > 1:
            strategy_status = "MIXED_INCOMPLETE"
        decisions = []
        bindings = []
        events = [{"event_type": "dynamic_grading_started"}]
        for c in claims:
            events.extend(
                [
                    {"event_type": "student_claim_extracted", "claim_id": c.claim_id},
                    {
                        "event_type": "dynamic_checker_completed",
                        "claim_id": c.claim_id,
                        "status": c.verification_status,
                    },
                ]
            )
        for criterion in rubric.criteria:
            policy, partial = criterion_policy(criterion)
            points = Decimal(0)
            suff = "INSUFFICIENT"
            auto = "REVIEW_ONLY"
            notes = []
            types = {
                "roots": {"ROOTS", "ROOT", "FORMULA"},
                "method": {"TRANSFORMATION", "FORMULA"},
                "factorization": {"TRANSFORMATION"},
                "transformation": {"TRANSFORMATION"},
                "substitution": {"SUBSTITUTION"},
            }.get(policy, set())
            evidence = [
                c
                for c in active
                if c.claim_type in types
                and (policy != "factorization" or c.strategy_context == "factorization")
            ]
            valid = [c for c in evidence if c.verification_status == "VERIFIED"]
            bad = [c for c in evidence if c.verification_status == "REFUTED"]
            unsafe = any(
                c.verification_status
                in {"ERROR", "REVIEW_ONLY", "INCOMPLETE", "NOT_ATTEMPTED"}
                for c in evidence
            )
            if conflict and policy in {"roots", "method", "factorization"}:
                suff = "CONFLICT"
                notes.append(
                    "Conclusões contraditórias adotadas; nenhuma foi escolhida silenciosamente."
                )
            elif policy and equation and not unsafe:
                if policy in {"roots", "substitution"}:
                    supplied = {
                        Fraction(v)
                        for c in evidence
                        if c.verification_status in {"VERIFIED", "REFUTED"}
                        for v in c.verified_values
                    }
                    ratio = Decimal(len(supplied & roots)) / Decimal(len(roots))
                    if ratio == 1 and not bad:
                        points = criterion.max_points
                        suff = "COMPLETE"
                        auto = "AUTO_AWARD"
                    elif partial and supplied:
                        points = (criterion.max_points * ratio).quantize(
                            Decimal(".01"), rounding=ROUND_DOWN
                        )
                        suff = "PARTIAL"
                        auto = "AUTO_AWARD"
                    elif bad and not supplied:
                        suff = "NOT_SATISFIED"
                        auto = "AUTO_VETO"
                else:
                    coverage, suff = method_coverage(policy, partial, evidence, answers, roots)
                    if coverage:
                        points = criterion.max_points if coverage == 1 else (
                            criterion.max_points * Decimal(coverage.numerator)
                            / Decimal(coverage.denominator)
                        ).quantize(Decimal(".01"), rounding=ROUND_DOWN)
                        auto = "AUTO_AWARD"
                    elif suff == "NOT_SATISFIED":
                        auto = "AUTO_VETO"
            prior = {d.criterion_id: d for d in decisions}
            if criterion.dependencies and any(
                dep not in prior or prior[dep].sufficiency != "COMPLETE"
                for dep in criterion.dependencies
            ):
                points = Decimal(0)
                auto = "REVIEW_ONLY"
                suff = "INSUFFICIENT"
                notes.append(
                    "Dependência/seguimento de erro anterior requer decisão docente; não há segundo veto automático."
                )
            if any(c.adoption in {"AMBIGUOUS", "HYPOTHETICAL"} for c in claims):
                points = Decimal(0)
                auto = "REVIEW_ONLY"
                suff = "INSUFFICIENT"
                notes.append("Contexto discursivo ambíguo.")
            if auto == "REVIEW_ONLY":
                notes.append(
                    "Zero é limite inferior provisório deste componente, não julgamento de erro."
                )
            if not policy:
                notes.append(
                    "Redação do critério fora da política executável v1; nenhuma condição foi descartada."
                )
            explanation = (
                f"{criterion.description} Evidências: "
                + (", ".join(c.claim_id for c in evidence) or "nenhuma")
                + f". {suff}: {points}/{criterion.max_points} pontos provisórios."
            )
            for c in evidence:
                bindings.append(
                    RubricBinding(
                        criterion_id=criterion.criterion_id,
                        claim_id=c.claim_id,
                        binding_type=policy,
                        evidence=c.text,
                        diagnostic_confidence="EXACT",
                        status="SUPPORTED",
                    )
                )
                events.append(
                    {
                        "event_type": "rubric_binding_created",
                        "criterion_id": criterion.criterion_id,
                        "claim_id": c.claim_id,
                    }
                )
            decision = DynamicRubricDecision(
                criterion_id=criterion.criterion_id,
                description=criterion.description,
                max_points=criterion.max_points,
                suggested_points=points,
                automation=auto,
                sufficiency=suff,
                claim_ids=[c.claim_id for c in evidence],
                checker_results=[
                    {
                        "claim_id": c.claim_id,
                        "status": c.verification_status,
                        "detail": c.verification_detail,
                    }
                    for c in evidence
                ],
                evidence=[c.text for c in evidence],
                explanation=explanation,
                review_required=auto == "REVIEW_ONLY",
                warnings=notes,
            )
            decisions.append(decision)
            events.append(
                {
                    "event_type": "dynamic_rubric_decision",
                    **decision.model_dump(mode="json"),
                }
            )
        if preparation.status == "REVIEW_REQUIRED":
            warnings.append(
                "Preparação com revisão necessária; execução explicitamente permitida, resultado provisório."
            )
        review = bool(warnings or conflict or any(d.review_required for d in decisions))
        if review:
            events.append({"event_type": "dynamic_review_required"})
        events.append({"event_type": "dynamic_grading_completed"})
        for i, event in enumerate(events):
            event.update(
                event_id=canonical_sha256(
                    {"source": source.source_hash, "index": i, "event": event}
                ),
                transcription_version=f"{source.transcription_id}:{source.revision_number}",
                package_id=context.package_id,
                preparation_id=context.preparation_id,
                rubric_id=context.rubric_id,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        try:
            code_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=get_repo_root(),
                capture_output=True,
                text=True,
                timeout=2,
                check=True,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            code_sha = None
        code_hash = canonical_sha256(
            {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(Path(__file__).parent.glob("*.py"))
            }
        )
        analysis = DynamicStudentSolutionAnalysis(
            transcription_version=f"{source.transcription_id}:{source.revision_number}",
            source_sha256=source.source_hash,
            segments=[
                s.model_dump(mode="json") for s in source.provenance.revision.segments
            ],
            claims=claims,
            strategy_status=strategy_status,
            strategy_candidate=strategy,
            final_answer_candidates=[c.text for c in answers],
            warnings=warnings,
            provenance={
                "grader": GRADER_VERSION,
                "extractor": EXTRACTOR_VERSION,
                "normalization": NORMALIZATION_VERSION,
                "verifier": VERSION,
                "model": None,
                "llm_used": False,
                "code_sha": code_sha,
                "code_content_sha256": code_hash,
                "policy": SUFFICIENCY_VERSION,
                "preparation_verifier_plan": [
                    p.model_dump(mode="json")
                    for p in preparation.analysis.verifier_plan
                ],
                "selected_capabilities": [
                    "EXACT_ARITHMETIC",
                    "SYMBOLIC_ALGEBRA",
                    "DETERMINISTIC",
                ],
                "selection_reason": "Plano DY2 preservado como contexto; verificadores locais selecionados pela forma do claim. Lean, capacidades numéricas e resíduo semântico não executados.",
            },
        )
        score = float(sum((d.suggested_points for d in decisions), Decimal(0)))
        items = [
            dict(
                id=d.criterion_id,
                description=d.description,
                points=float(d.suggested_points),
                max_points=float(d.max_points),
                mathematical_status=(
                    "indeterminate"
                    if d.review_required
                    else "supported" if d.automation == "AUTO_AWARD" else "refuted"
                ),
                verification_status=(
                    "review_only"
                    if d.review_required
                    else (
                        "verified_in_scope"
                        if d.automation == "AUTO_AWARD"
                        else "refuted_exact"
                    )
                ),
                evidence="\n".join(d.evidence),
                assessment_note=d.explanation,
                adjustment_notes=d.warnings,
            )
            for d in decisions
        ]
        result = DynamicAuditResult(
            problem_id=source.problem_id,
            context=context,
            score=score,
            suggested_score=score,
            max_score=float(rubric.max_score),
            review_required=review,
            verdict="inconclusivo" if review else "concluido",
            uncertainty=warnings,
            reviewed_components=[
                d.criterion_id for d in decisions if not d.review_required
            ],
            unreviewed_components=[
                d.criterion_id for d in decisions if d.review_required
            ],
            analysis=analysis,
            bindings=bindings,
            decisions=decisions,
            events=events,
            rubric_assessment={
                "assessment_status": "partial" if review else "complete",
                "items": items,
            },
            feedback="Sugestão provisória calculada por critérios. "
            + (
                "Revisão necessária; componentes não resolvidos não receberam crédito automático."
                if review
                else "Verificações exatas no escopo declarado; decisão final do professor."
            ),
            artifact_dir=str(Path(artifact_dir).absolute()),
        )
        from .semantic import enabled, augment
        if enabled(context):
            result = augment(result, source, statement, rubric)
            analysis = result.analysis
        root = Path(result.artifact_dir)
        root.mkdir(parents=True, exist_ok=False)
        for name, value in [
            ("audit.json", result.model_dump(mode="json")),
            ("analysis.json", analysis.model_dump(mode="json")),
            (
                "context.json",
                {
                    "context": context.model_dump(mode="json"),
                    "statement": statement.model_dump(mode="json"),
                    "rubric": rubric.model_dump(mode="json"),
                    "preparation": preparation.model_dump(mode="json"),
                },
            ),
        ]:
            (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2))
        (root / "solution.txt").write_text(source.solution_text)
        return result
