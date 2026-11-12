"""Phase A cannot access a grader result. Mathematical checking is not judgment reuse."""

from copy import deepcopy
from decimal import Decimal, ROUND_DOWN
from fractions import Fraction
from datetime import datetime, timezone
from .grader import extract, problem_equation, criterion_policy, plain
from .review_models import BlindReviewProposal, CriterionReview, IndependentPhase
from .provider import ProviderFailure
from confia_lean_auditor.submissions.integrity import canonical_sha256


def evidence_inventory(solution, statement):
    try:
        equation = problem_equation(statement.statement)
        claims, warnings = extract(solution, equation)
        # IDs have a different namespace; no reuse of DY3 decomposition as complete.
        for claim in claims:
            claim.claim_id = "review_" + claim.claim_id
        return equation, claims, warnings
    except (ValueError, ZeroDivisionError, OverflowError):
        return None, [], ["Enunciado fora do escopo verificável; revisão necessária."]


def blind_input(source, statement, rubric, preparation, context):
    equation, claims, warnings = evidence_inventory(source.solution_text, statement)
    payload = dict(
        statement=statement.model_dump(mode="json"),
        approved_rubric=rubric.model_dump(mode="json"),
        preparation=preparation.model_dump(mode="json"),
        solution=source.solution_text,
        transcription_version_id=f"{source.transcription_id}:{source.revision_number}",
        source_sha256=source.source_hash,
        context=context.model_dump(mode="json", exclude={"grader_version"}),
        mathematical_evidence=[c.model_dump(mode="json") for c in claims],
        verification_policy={
            "version": "dynamic-review-evidence.v1",
            "reuse": "Fresh exact checks from the accepted source. DY3 does not provide a separate proposition-bound verification receipt; grader fidelity flags are not trusted as proof. Checks are executed once per claim and reused across criteria; no Lean rerun.",
            "pedagogical_scope": "Use only approved obligations. Do not invent extra explanations or percentage deductions. Unsupported sufficiency is uncertainty, not a safe point proposal.",
        },
        warnings=warnings,
    )
    return payload, equation, claims


def additional_evidence(proposal, solution, equation):
    added = []
    rejected = []
    for item in proposal.additional_claims:
        reason = None
        if (
            not equation
            or item.end <= item.start
            or solution[item.start : item.end] != item.quote
        ):
            reason = "Trecho não corresponde à fonte."
        # Only a whole mathematical segment or an explicit connective is supported.
        before = (
            max(solution.rfind(";", 0, item.start), solution.rfind("\n", 0, item.start))
            + 1
        )
        ends = [
            i
            for i in (solution.find(";", item.end), solution.find("\n", item.end))
            if i >= 0
        ]
        after = min(ends) if ends else len(solution)
        prefix = plain(solution[before : item.start]).strip()
        suffix = solution[item.end : after].strip()
        if prefix not in {
            "",
            "logo,",
            "portanto,",
            "assim,",
            "concluo:",
        } or suffix not in {"", "."}:
            reason = "Contexto não adotado ou fidelidade insuficiente; não recortar hipótese/negação."
        if reason:
            rejected.append(
                dict(claim_id=item.claim_id, reason=reason, quote=item.quote)
            )
            continue
        local, _ = extract(item.quote, equation)
        if (
            len(local) != 1
            or local[0].fidelity not in {"FAITHFUL", "SUPPORTED_NORMALIZATION"}
            or local[0].adoption != "ADOPTED"
        ):
            rejected.append(
                dict(
                    claim_id=item.claim_id,
                    reason="Representação adicional não suportada.",
                    quote=item.quote,
                )
            )
            continue
        c = local[0]
        c.claim_id = item.claim_id
        c.start += item.start
        c.end += item.start
        added.append(c)
    return added, rejected


def independent_limit(criterion, evidence, equation, all_claims):
    """Independent obligation coverage; shares exact math/criterion language, not DY3 decisions."""
    policy, partial = criterion_policy(criterion)
    if not policy or not equation:
        return (
            None,
            "INSUFFICIENT",
            ["Obrigação pedagógica fora do escopo automatizável."],
        )
    if any(c.adoption in {"HYPOTHETICAL", "AMBIGUOUS"} for c in all_claims):
        return None, "CONFLICT", ["Contexto ambíguo; pontuação não é segura."]
    active = [
        c
        for c in all_claims
        if c.adoption == "ADOPTED"
        and c.fidelity in {"FAITHFUL", "SUPPORTED_NORMALIZATION"}
    ]
    answers = [c for c in active if c.claim_type in {"ROOT", "ROOTS", "FORMULA"}]
    sets = {tuple(sorted(c.values)) for c in answers if c.claim_type == "ROOTS"}
    if policy in {"roots", "method", "factorization"} and (
        len(sets) > 1
        or any(c.verification_status == "REFUTED" for c in answers)
        and any(c.verification_status == "VERIFIED" for c in answers)
    ):
        return None, "CONFLICT", ["Conclusões adotadas em conflito."]
    types = {
        "roots": {"ROOT", "ROOTS", "FORMULA"},
        "substitution": {"SUBSTITUTION"},
        "method": {"TRANSFORMATION", "FORMULA"},
        "factorization": {"TRANSFORMATION"},
        "transformation": {"TRANSFORMATION"},
    }[policy]
    relevant = lambda c: c.claim_type in types and (
        policy != "factorization" or c.strategy_context == "factorization"
    )
    chosen = [
        c
        for c in evidence
        if relevant(c)
        and c.adoption == "ADOPTED"
        and c.fidelity in {"FAITHFUL", "SUPPORTED_NORMALIZATION"}
    ]
    auxiliary = [
        c
        for c in evidence
        if policy in {"method", "factorization"}
        and c.claim_type in {"ARITHMETIC", "ROOT", "ROOTS"}
        and c.adoption == "ADOPTED"
        and c.fidelity in {"FAITHFUL", "SUPPORTED_NORMALIZATION"}
        and c.verification_status == "VERIFIED"
    ]
    # Auxiliary arithmetic/conclusion can support an argument, never replace its development.
    if len(chosen) + len(auxiliary) != len(evidence):
        return (
            None,
            "INSUFFICIENT",
            ["Binding ou fidelity incompatível com este critério."],
        )
    if any(c.verification_status not in {"VERIFIED", "REFUTED"} for c in chosen):
        return None, "INSUFFICIENT", ["Verificador inconclusivo ou com erro."]
    good = [c for c in chosen if c.verification_status == "VERIFIED"]
    bad = [c for c in active if relevant(c) and c.verification_status == "REFUTED"]
    roots = equation[-1]
    maximum = criterion.max_points
    if policy in {"roots", "substitution"}:
        supplied = {Fraction(v) for c in chosen for v in c.verified_values} & roots
        if supplied == roots and not bad:
            return maximum, "COMPLETE", []
        if supplied and partial:
            return (
                (maximum * Decimal(len(supplied)) / Decimal(len(roots))).quantize(
                    Decimal(".01"), rounding=ROUND_DOWN
                ),
                "PARTIAL",
                [],
            )
        return (
            Decimal(0),
            "NOT_SATISFIED" if bad and not supplied else "INSUFFICIENT",
            [],
        )
    if bad:
        return (
            Decimal(0),
            "NOT_SATISFIED",
            ["Desenvolvimento contém afirmação refutada."],
        )
    if policy == "transformation" and good:
        return maximum, "COMPLETE", []
    explicit_roots = {
        Fraction(v)
        for c in answers
        if c.verification_status == "VERIFIED"
        for v in c.verified_values
    }
    formula = {
        Fraction(v)
        for c in good
        if c.claim_type == "FORMULA"
        for v in c.verified_values
    }
    factored = any(c.strategy_context == "factorization" for c in good)
    if good and (
        formula == roots
        or factored
        and explicit_roots == roots
        or max(equation[3]) == 1
        and explicit_roots == roots
    ):
        return maximum, "COMPLETE", []
    return (
        Decimal(0),
        "INSUFFICIENT",
        ["Resposta final não supre justificativa ausente."],
    )


class IndependentDynamicReviewer:
    def __init__(self, provider):
        self.provider = provider

    def analyze(self, payload, equation, claims, rubric):
        # Provider sees only this explicit allowlist, never an AuditRun/result object.
        proposal, meta = self.provider.generate(deepcopy(payload), BlindReviewProposal)
        proposal = BlindReviewProposal.model_validate(proposal)
        ids = [x.criterion_id for x in proposal.criterion_reviews]
        extra = [x.claim_id for x in proposal.additional_claims]
        if (
            len(ids) != len(set(ids))
            or set(ids) != {c.criterion_id for c in rubric.criteria}
            or len(extra) != len(set(extra))
        ):
            raise ProviderFailure("REVIEWER_INVALID_BINDINGS")
        if (
            meta.input_sha256 != canonical_sha256(payload)
            or meta.output_sha256 != canonical_sha256(meta.raw_output)
            or BlindReviewProposal.model_validate_json(meta.raw_output) != proposal
        ):
            raise ProviderFailure("REVIEWER_PROVENANCE_MISMATCH")
        added, rejected = additional_evidence(proposal, payload["solution"], equation)
        inventory = {c.claim_id: c for c in [*claims, *added]}
        reviews = []
        proposals = {p.criterion_id: p for p in proposal.criterion_reviews}
        for criterion in sorted(rubric.criteria, key=lambda c: c.order):
            p = proposals[criterion.criterion_id]
            points = (
                Decimal(p.proposed_points) if p.proposed_points is not None else None
            )
            if points is not None and points > criterion.max_points:
                raise ProviderFailure("REVIEWER_POINTS_OUT_OF_RANGE")
            evidence = [inventory[k] for k in p.claim_ids if k in inventory]
            limit, suff, warnings = independent_limit(
                criterion, evidence, equation, list(inventory.values())
            )
            if len(evidence) != len(p.claim_ids) or len(p.claim_ids) != len(
                set(p.claim_ids)
            ):
                limit = None
                warnings.append("Referência de claim inválida ou duplicada.")
            previous = {r.criterion_id: r for r in reviews}
            if any(
                dep not in previous or previous[dep].sufficiency != "COMPLETE"
                for dep in criterion.dependencies
            ):
                limit = None
                suff = "INSUFFICIENT"
                warnings.append(
                    "Follow-through depende de política/evidência adicional; não aplicar veto duplicado."
                )
            if points is not None and (limit is None or points > limit):
                warnings.append(
                    "Proposta do reviewer não sustentada pelas verificações; revisão humana necessária."
                )
            accepted = (
                points
                if limit is not None and points is not None and points <= limit
                else None
            )
            if accepted is not None and accepted < limit:
                accepted = None
                warnings.append(
                    "O reviewer propôs menos que a cobertura verificável; suficiência requer revisão."
                )
            uncertain = bool(
                warnings
                or p.uncertainty
                or accepted is None
                or suff in {"INSUFFICIENT", "CONFLICT"}
                or p.assessment != suff
            )
            reviews.append(
                CriterionReview(
                    criterion_id=criterion.criterion_id,
                    max_points=criterion.max_points,
                    proposed_points=accepted,
                    provider_proposed_points=points,
                    assessment=(
                        "REVIEW_REQUIRED"
                        if uncertain
                        else (
                            "SATISFIED"
                            if suff == "COMPLETE"
                            else (
                                "PARTIALLY_SATISFIED"
                                if suff == "PARTIAL"
                                else "NOT_SATISFIED"
                            )
                        )
                    ),
                    sufficiency=suff,
                    claim_ids=p.claim_ids,
                    evidence=[c.text for c in evidence],
                    checker_references=[
                        dict(
                            claim_id=c.claim_id,
                            status=c.verification_status,
                            components=c.components,
                            start=c.start,
                            end=c.end,
                        )
                        for c in evidence
                    ],
                    explanation=p.explanation,
                    uncertainty=[*p.uncertainty, *warnings],
                    review_required=uncertain,
                )
            )
        warnings = [*proposal.warnings, *payload["warnings"]]
        if rejected:
            warnings.append("Claims adicionais recusadas por fidelity/contexto.")
        if payload["preparation"]["status"] == "REVIEW_REQUIRED":
            warnings.append("Preparação mantém avisos de revisão docente.")
        return IndependentPhase(
            criterion_reviews=reviews,
            claims=claims,
            additional_claims=added,
            rejected_claims=rejected,
            detected_strategy=proposal.detected_strategy,
            alternative_strategy=proposal.alternative_strategy,
            warnings=warnings,
            review_required=bool(warnings or any(r.review_required for r in reviews)),
            proposal=proposal,
            provenance=meta,
            input_sha256=canonical_sha256(payload),
            completed_at=datetime.now(timezone.utc),
        )
