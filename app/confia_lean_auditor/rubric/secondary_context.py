"""Minimal adjudicator context assembled from existing rubric/evidence contracts."""
from . import secondary_adjudicator as secondary
from .positive_evidence import rules, related_check_types
from confia_lean_auditor.student_claims.grounding import source_matches
from confia_lean_auditor.claims.common.bridges import matching_student_check
from .secondary_candidates import with_candidates
from .secondary_award_gate import answer_only
from confia_lean_auditor.lean.microclaim_evaluator import locally_verified, dependencies_are_verified


def _dump(value):
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def prepare_payload(*, pending, solution, assets, microclaims, student_checks, claim_context=None):
    """Preserve primary results; expose rubric prerequisites to secondary safety."""
    official = {item.id: item for item in assets.rubric.items}
    problem = _dump(assets.problem)
    pid = problem.get("id", "")
    observed_microclaims = {m.id: m for m in microclaims}
    microclaim_config = getattr(assets, "microclaims", None)
    declared_microclaims = {m.id: m for m in getattr(microclaim_config, "microclaims", ())}
    rows = []
    for item in pending:
        if item.mathematical_status not in (None, "indeterminate"):
            raise secondary.AdjudicationError("ADJUDICATOR_INVALID_CRITERIA",
                category="primary_status_not_eligible", criterion_id=item.id)
        config = official[item.id]
        claim_type = getattr(config, "claim_type", None)
        rule = rules().get((pid, claim_type))
        required = getattr(config, "required_microclaim_ids", ())
        required_context = []
        for identifier in required:
            declaration = declared_microclaims.get(identifier) or observed_microclaims.get(identifier)
            observed = observed_microclaims.get(identifier)
            required_context.append({
                "description": declaration.description if declaration else "Requisito declarado sem descrição disponível",
                "status": observed.lean_status if observed else "unavailable",
                "satisfied": bool(observed and locally_verified(observed)
                                  and dependencies_are_verified(observed.depends_on_microclaim_ids, observed_microclaims)),
                "origin": "generated_reference", "does_not_prove_student_attribution": True})
        requirements = []
        if rule:
            for requirement in rule.requirements:
                requirements.append({"description": requirement.label,
                    "relation_alternatives": [list(p.equations) for p in requirement.patterns
                                              if getattr(p, "equations", ())]})
        related_types = set(related_check_types(pid, item.id)) if pid else set()
        checks = [c for c in student_checks if c.get("problem_id") == pid
                  and c.get("claim_type") in related_types and source_matches(c, solution)]
        grounded = []
        if claim_context:
            relevant_ids = set()
            alignments = {}
            for reference in (*claim_context.references, *claim_context.expected_records):
                if item.id not in reference.rubric_links:
                    continue
                alignment = claim_context.alignment(reference)
                relevant_ids.update(alignment.student_record_ids)
                for identifier in alignment.student_record_ids:
                    alignments.setdefault(identifier, []).append({"status": alignment.status,
                                                                 "basis": alignment.alignment_basis})
            for student in claim_context.students:
                if not (student.source.attributable and student.source.grounding_status == "grounded"):
                    continue
                if student.record_id not in relevant_ids and student.claim_type not in related_types:
                    continue
                # This invokes the unchanged P0 projection/source validation.
                matched = [c for c in checks if matching_student_check(student, c,
                    solution_text=solution, statement_text=problem.get("statement", ""))]
                grounded.append({"text": student.source.raw_text,
                    "math_claim_record_id": student.record_id,
                    "source_span": {"start": student.source.source_start, "end": student.source.source_end},
                    "semantic_role": str(student.semantic_role.value),
                    "canonical_form": _dump(student.canonical_form) if student.canonical_form else None,
                    "alignment": alignments.get(student.record_id, []),
                    "verification": [{k: c.get(k) for k in ("status", "formal_status", "compiled",
                                                             "refutation_verified")} for c in matched]})
        rows.append({"id": item.id, "description": config.description,
            "max_points": item.max_points, "allowed_points": [0.0, item.max_points],
            "input_status": item.mathematical_status or "legacy_undecided",
            "verification_status": item.verification_status,
            "coded_requirements": requirements,
            "answer_only": answer_only({"description": config.description,
                                       "conclusion_only": bool(rule and rule.conclusion_only)}),
            "conclusion_only": bool(rule and rule.conclusion_only),
            "allowed_mathematical_negations": list(rule.allowed_negations) if rule else [],
            "required_microclaims": required_context,
            "existing_evidence": [item.evidence] if item.evidence and item.evidence in solution else [],
            "grounded_claims": grounded[:12], "grounded_claims_omitted": max(0, len(grounded)-12),
            # Untruncated local safety context: a contradictory claim beyond the
            # retrieval budget must not silently disappear from the award gate.
            "award_grounded_claims": grounded,
            "award_verification_results": checks,
            "candidate_student_checks": checks[:12],
            "student_checks": [{k: c.get(k) for k in ("claim_type", "raw_text", "status", "formal_status",
                "compiled", "failure_category", "refutation_verified")} for c in checks[:12]]})
    # Full source remains local for exact binding checks; only candidates go on wire.
    return with_candidates({"problem": {"statement": problem.get("statement", "")},
            "solution_text": solution, "pending_criteria": rows}, secondary.redact)
