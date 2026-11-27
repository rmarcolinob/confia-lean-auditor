"""Map already verified auditor facts to obligations, without interpreting math.

Claims remain MathClaimRecord; FactResult is a verification result referencing
those records, not another claim representation. This module never takes text.
"""
import hashlib
import json
from typing import Any, Literal, Optional

from pydantic import Field, model_validator

from confia_lean_auditor.claims.common.schemas import MathClaimRecord, Origin, SemanticRole, VerificationLink
from .models import Contract, Identifier, ObligationEvidence, PautaConfig, PautaEvidence, ConditionalContext

PILOT_ID = "TME2_P1_PILOT"
# These are fact-to-obligation identities, not scoring rules or point values.
TME2_P1_OBLIGATIONS = {
    "a.inverted_number_137": "a.identifies_137",
    "a.subtraction_731_137": "a.constructs_subtraction",
    "a.result_594": "a.result_594",
    "a.single_arithmetic_error": "a.arithmetic_error_only",
    "b.reversed_number": "b.reversed_number",
    "b.subtraction": "b.subtraction",
    "b.middle_cancellation": "b.middle_cancellation",
    "b.factorization": "b.factorization",
    "c.uses_expression": "c.uses_expression",
    "c.difference_domain": "c.difference_domain",
    "c.complete_list": "c.complete_list",
    "c.no_extraneous_values": "c.no_extraneous_values",
    "c.single_list_error": "c.single_list_error",
    "c.several_correct": "c.several_correct",
    "c.pattern_recognized": "c.pattern_recognized",
    "c.some_correct": "c.some_correct",
    "d.equation": "d.equation",
    "d.difference_six": "d.difference_six",
    "d.digit_pairs": "d.digit_pairs",
    "d.middle_choices": "d.middle_choices",
    "d.total_thirty": "d.total_thirty",
}


def record_fingerprint(record):
    value = json.dumps(record.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode()).hexdigest()


class FactResult(Contract):
    fact_id: Identifier
    source_claim_ids: tuple[Identifier, ...]
    record_fingerprints: dict[str, str]
    verification: VerificationLink
    verification_source: Literal["deterministic", "canonical_equivalence", "student_lean",
                                 "reference_lean", "semantic", "secondary"]
    # Original StudentClaimCheck payload, only for the real student Lean route.
    student_check: Optional[dict[str, Any]] = None
    conditional_on: Optional[ConditionalContext] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def references(self):
        if not self.source_claim_ids or len(set(self.source_claim_ids)) != len(self.source_claim_ids):
            raise ValueError("A fact result requires unique existing source claims")
        if set(self.record_fingerprints) != set(self.source_claim_ids):
            raise ValueError("Bind verification to every exact input record")
        if not self.verification.verification_id or not self.verification.artifact_ref:
            raise ValueError("Verification identity and reference are required")
        return self


class AuditorFactBundle(Contract):
    schema_version: Literal["auditor-pauta-facts.v1"] = "auditor-pauta-facts.v1"
    problem_id: Identifier
    solution_id: Identifier
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    records: tuple[MathClaimRecord, ...]
    facts: tuple[FactResult, ...]

    @model_validator(mode="after")
    def identities(self):
        ids = [r.record_id for r in self.records]
        checks = [f.verification.verification_id for f in self.facts]
        if len(set(ids)) != len(ids) or len(set(checks)) != len(checks):
            raise ValueError("Duplicate record or verification identities")
        if any(r.problem_id != self.problem_id for r in self.records):
            raise ValueError("Record belongs to another problem")
        if any(not set(f.source_claim_ids) <= set(ids) for f in self.facts):
            raise ValueError("Fact points to a nonexistent claim")
        return self


class PautaBridgeResult(Contract):
    schema_version: Literal["pauta-bridge.v1"] = "pauta-bridge.v1"
    evidence: PautaEvidence
    auditor: AuditorFactBundle


def _formal_result_matches(fact, records):
    """Check identity/attribution of a saved result; never run or infer a proof."""
    check = fact.student_check
    if not check:
        return False
    matches = [r for r in records if r.provenance.legacy_id == check.get("id")]
    if len(matches) != 1:
        return False
    record = matches[0]
    if any(r.source != record.source for r in records):
        return False
    payload = record.legacy_payload or {}
    g = check.get("grounding") or {}
    if (record.provenance.legacy_id != check.get("id")
            or record.problem_id != check.get("problem_id")
            or record.claim_type != check.get("claim_type")
            or payload.get("data") != check.get("data")
            or payload.get("grounding") != g
            or g.get("source_text") != record.source.raw_text
            or g.get("source_start") != record.source.source_start
            or g.get("source_end") != record.source.source_end
            or g.get("source_sha256") != record.source.source_sha256
            or check.get("verification_scope") == "generated_reference"):
        return False
    status = fact.verification.status
    if status == "technical_error":
        return check.get("status") == "technical_error"
    if status == "verified":
        return (check.get("status") == "verified" and check.get("formal_status") == "verified"
                and check.get("compiled") is True and bool(check.get("lean_file")))
    if status == "refuted":
        return (check.get("status") == "refuted" and check.get("formal_status") == "refuted"
                and check.get("refutation_verified") is True and bool(check.get("refutation_lean_file")))
    return check.get("status") == status


def _validated_status(fact, records, digest, structured_fact_ids=()):
    from confia_lean_auditor.claims.common.schemas import StructuredSourceBinding
    if any(isinstance(r.source, StructuredSourceBinding) for r in records) and fact.verification_source != 'deterministic':
        return "indeterminate", "DIAGRAM_REQUIRES_DETERMINISTIC_VERIFICATION"
    if any(isinstance(r.source, StructuredSourceBinding) for r in records) and fact.fact_id not in structured_fact_ids:
        return "indeterminate", "STRUCTURED_FACT_NOT_ENABLED_FOR_THIS_BRIDGE"
    if any(record_fingerprint(r) != fact.record_fingerprints[r.record_id] for r in records):
        return "indeterminate", "RECORD_CHANGED_AFTER_VERIFICATION"
    if any(not r.source.attributable or r.source.grounding_status != "grounded"
           or r.source.source_sha256 != digest or r.provenance.origin not in
           {Origin.STUDENT_EXPLICIT, Origin.STUDENT_DERIVED}
           or r.semantic_role in {SemanticRole.ASSUMPTION, SemanticRole.QUOTED_STATEMENT,
                                  SemanticRole.REJECTED_ATTEMPT} for r in records):
        return "indeterminate", "SOURCE_NOT_ATTRIBUTABLE"
    link = fact.verification
    if any(link not in r.verification_results for r in records):
        return "indeterminate", "VERIFICATION_LINK_NOT_ON_SOURCE_RECORD"
    if not link.attributed_to_student or link.origin not in {Origin.STUDENT_EXPLICIT, Origin.STUDENT_DERIVED}:
        return "indeterminate", "VERIFICATION_NOT_ATTRIBUTED_TO_STUDENT"
    if fact.verification_source not in {"deterministic", "canonical_equivalence", "student_lean"}:
        return "indeterminate", "VERIFICATION_SOURCE_NOT_ENABLED_FOR_PILOT"
    if fact.verification_source == "student_lean" and not _formal_result_matches(fact, records):
        return "indeterminate", "STUDENT_LEAN_RESULT_NOT_BOUND"
    status = {"verified": "supported", "refuted": "refuted", "technical_error": "technical_error"}.get(link.status, "indeterminate")
    return status, "EXISTING_VERIFICATION_RESULT"


def bridge_tme2_p1(config: PautaConfig, bundle: AuditorFactBundle) -> PautaBridgeResult:
    """Only P1; consume statuses and provenance, never expressions or points."""
    return bridge_facts(config, bundle, problem_id=PILOT_ID,
        obligation_map=TME2_P1_OBLIGATIONS, mapping_version="tme2-p1-obligations.v1")


def bridge_facts(config: PautaConfig, bundle: AuditorFactBundle, *, problem_id,
                 obligation_map, mapping_version, structured_fact_ids=()) -> PautaBridgeResult:
    """Shared explicit mapping, with exactly the P1 attribution/status gates."""
    config = PautaConfig.model_validate(config.model_dump())
    bundle = AuditorFactBundle.model_validate(bundle.model_dump())
    if config.problem_id != problem_id or bundle.problem_id != problem_id:
        raise ValueError("This bridge is restricted to its declared problem")
    if {o.id for o in config.obligations} != set(obligation_map.values()):
        raise ValueError("Pilot obligation contract changed")
    if any(f.fact_id not in obligation_map for f in bundle.facts):
        raise ValueError("Unmapped fact: no heuristic assignment to an obligation")
    by_id = {r.record_id: r for r in bundle.records}
    output = []
    for fact_id, obligation_id in obligation_map.items():
        facts = [f for f in bundle.facts if f.fact_id == fact_id]
        ids = tuple(dict.fromkeys(i for f in facts for i in f.source_claim_ids))
        records = [by_id[i] for i in ids]
        checks = [_validated_status(f, [by_id[i] for i in f.source_claim_ids], bundle.source_sha256,
                                    structured_fact_ids) for f in facts]
        states = {s for s, _ in checks}
        if not facts:
            status, reason = "indeterminate", "NO_EXISTING_FACT"
        elif {"supported", "refuted"} <= states:
            status, reason = "indeterminate", "CONFLICTING_FACT_RESULTS"
        elif "technical_error" in states:
            status, reason = "technical_error", "UPSTREAM_TECHNICAL_ERROR"
        elif "indeterminate" in states:
            status, reason = "indeterminate", "UNRESOLVED_FACT_RESULT"
        else:
            status, reason = next(iter(states)), "MAPPED_VERIFIED_FACT"
        contexts = [f.conditional_on for f in facts]
        if contexts and any(c != contexts[0] for c in contexts[1:]):
            status, reason = "indeterminate", "CONFLICTING_CONDITIONAL_CONTEXTS"
        mechanisms = {f.verification_source for f in facts}
        mechanism = next(iter(mechanisms)) if len(mechanisms) == 1 else "deterministic"
        origin = "deterministic" if mechanism == "canonical_equivalence" else mechanism
        grounding = ("ambiguous" if any(r.source.grounding_status == "ambiguous" for r in records)
            else "grounded" if records and all(r.source.grounding_status == "grounded"
                and r.source.source_sha256 == bundle.source_sha256 for r in records)
            else "unresolved" if records else "unavailable")
        output.append(ObligationEvidence(
            obligation_id=obligation_id, status=status, origin=origin,
            evidence_refs=tuple(dict.fromkeys([*ids, *(f.verification.artifact_ref for f in facts)])),
            attributable_to_student=bool(records) and grounding == "grounded" and all(r.source.attributable for r in records),
            source_claim_ids=ids, verification_source=mechanism, grounding_status=grounding,
            conditional_on=contexts[0] if contexts and all(c == contexts[0] for c in contexts) else None,
            metadata={"fact_id": fact_id, "mapping_version": mapping_version, "reason": reason,
                "source_sha256": bundle.source_sha256,
                "verifications": [{"verification_id": f.verification.verification_id,
                    "verification_source": f.verification_source, "effective_status": s,
                    "reason": r, "metadata": f.metadata} for f, (s, r) in zip(facts, checks)]},
        ))
    return PautaBridgeResult(evidence=PautaEvidence(problem_id=bundle.problem_id,
        solution_id=bundle.solution_id, obligations=tuple(output)), auditor=bundle)
