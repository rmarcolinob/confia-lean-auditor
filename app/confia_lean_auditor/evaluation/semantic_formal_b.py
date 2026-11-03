"""Isolated orchestration of the frozen builders, checkers and credit gate."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
from importlib import import_module
from pathlib import Path
import time

from confia_lean_auditor.core.problem_assets import validate_problem_assets
from confia_lean_auditor.core.schemas import LeanCertificate
from confia_lean_auditor.student_claims.registry import extract_student_claims
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck
from confia_lean_auditor.lean.student_claim_checkers.registry import check_student_claims_for_problem
from confia_lean_auditor.lean.formal_step_evaluator import evaluate_formal_steps
from confia_lean_auditor.lean.build_attempt import build_attempt
from confia_lean_auditor.lean.run_lean import run_lean_file
from confia_lean_auditor.lean.microclaim_evaluator import evaluate_microclaims
from confia_lean_auditor.semantic.semantic_extractor_v2 import extract_semantic_claims, SemanticExtractionError
from confia_lean_auditor.semantic.semantic_claim_adapter import adapt_claim, evidence_bridge
from confia_lean_auditor.semantic.evidence_unit import EvidenceUnit, from_historical_claim, from_semantic_claim
from .formal_award_gate import formal_award_gate, AWARD_POLICY
from .structural_metrics import case_metrics


@contextmanager
def checker_paths(repo_root, output_dir, problem_id):
    """Serial adapter: restore imported globals even on technical failure."""
    base = import_module("confia_lean_auditor.lean.student_claim_checker")
    specific = import_module("confia_lean_auditor.lean.student_claim_checkers." + problem_id.lower())
    old_root, old_dir = base.ROOT_DIR, specific.CHECK_DIR
    base.ROOT_DIR, specific.CHECK_DIR = repo_root, output_dir
    try:
        yield
    finally:
        base.ROOT_DIR, specific.CHECK_DIR = old_root, old_dir


def run_checks(repo_root, output_dir, problem_id, claims):
    checks = []
    with checker_paths(repo_root, output_dir, problem_id):
        # Per-claim catching preserves completed checks and always gives a numeric case.
        for index, claim in enumerate(claims):
            try:
                completed = check_student_claims_for_problem(problem_id, [claim], f"check_{index:04d}")
                for checked in completed:
                    for field in ("stdout", "stderr"):
                        value = getattr(checked, field)
                        if isinstance(value, bytes):
                            setattr(checked, field, value.decode("utf-8", errors="replace"))
                checks.extend(completed)
            except Exception as exc:
                checks.append(StudentClaimCheck(id=claim.id, problem_id=problem_id,
                    claim_type=claim.claim_type, raw_text=claim.raw_text,
                    normalized_text=claim.normalized_text, lean_statement="", method=claim.method,
                    status="error", compiled=False, lean_file=None, stdout="",
                    stderr=f"{type(exc).__name__}: {exc}", data=claim.data))
    return checks


def run_formal_chain(repo_root, output_dir, problem_id, extraction, assets):
    steps = evaluate_formal_steps(repo_root, problem_id, extraction, output_dir)
    attempt = build_attempt(repo_root, problem_id, extraction, output_dir, steps)
    raw = run_lean_file(repo_root, attempt["attempt_path"])
    certificate = LeanCertificate(**raw, lean_file=str(attempt["attempt_path"]),
                                  generated_theorems=attempt["generated_theorems"])
    micros = evaluate_microclaims(repo_root, problem_id, extraction, certificate,
        attempt["generated_theorems"], steps, assets.microclaims)
    return micros, {"certificate": certificate.model_dump(mode="json"),
                           "formal_steps": [s.model_dump(mode="json") for s in steps]}


def evaluate_mode(repo_root, output_dir, problem_id, solution, mode, evidence=()):
    """Mode-specific extraction boundary only; all downstream processing is shared."""
    if mode == "FORMAL_OFFLINE":
        units = [from_historical_claim(c, problem_id, solution)
                 for c in extract_student_claims(problem_id, solution)]
    elif mode == "SEMANTIC_FORMAL":
        units = [from_semantic_claim(c, problem_id, solution) for c in evidence]
    else:
        raise ValueError("Unknown extraction mode")
    return evaluate_evidence(repo_root, output_dir, problem_id, solution, units)


def evaluate_evidence(repo_root, output_dir, problem_id, solution, evidence: list[EvidenceUnit]):
    """One adapter → checkers → obligation bridge → Lean → gate → score pipeline."""
    output_dir.mkdir(parents=True, exist_ok=False)
    assets = validate_problem_assets(repo_root / "problems" / problem_id, problem_id)
    claims = [adapt_claim(e, problem_id, solution) for e in evidence]
    extracted = [e.model_dump(mode="json") for e in evidence]
    checks = run_checks(repo_root, output_dir / "student_claim_checks", problem_id, claims)
    extraction = evidence_bridge(repo_root, problem_id, evidence, checks)
    errors = [c.stderr for c in checks if c.status == "error"]
    try:
        micros, lean = run_formal_chain(repo_root, output_dir, problem_id, extraction, assets)
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
        micros, lean = [], {"certificate": {"status": "error"}, "formal_steps": []}
    rubric, decisions = formal_award_gate(problem_id, evidence, checks, micros, extraction, assets.rubric)
    environment_markers = ("unknown module prefix", "object file", "unknown identifier", "no such file", "failed to fetch", "could not download")
    diagnostics = "\n".join([c.stdout + "\n" + c.stderr for c in checks]
        + [str(lean["certificate"].get("stdout", "")) + str(lean["certificate"].get("stderr", ""))]).lower()
    if any(marker in diagnostics for marker in environment_markers):
        errors.append("Lean environment/import failure; see recorded stdout/stderr")
    statuses = [c.status for c in checks] + [s["status"] for s in lean["formal_steps"]]
    statuses.append(lean["certificate"]["status"])
    if errors or "error" in statuses or any("timeout" in s or "unknown_identifier" in s for s in statuses):
        lean_status = "technical_error"
    elif any(s != "verified" for s in statuses):
        lean_status = "not_all_verified"
    else:
        lean_status = "verified"
    return {"award_policy": AWARD_POLICY, "score": rubric.score, "rubric_items": [i.model_dump(mode="json") for i in rubric.items],
        "extracted_evidence": extracted, "student_claim_checks": [asdict(c) for c in checks],
        "formal_award_decisions": decisions, "lean_status": lean_status, "lean": lean,
        "microclaims": [m.model_dump(mode="json") for m in micros],
        "claim_extraction": extraction.model_dump(mode="json"), "technical_errors": errors}


def evaluate_case(repo_root, output_dir, case, mode, model, reasoning_effort=None,
                  extractor=extract_semantic_claims, evaluator=evaluate_mode):
    start = time.perf_counter()
    requested = mode.upper()
    if requested not in {"FORMAL_OFFLINE", "SEMANTIC_FORMAL"}:
        raise ValueError("Unknown mode")
    effective, fallback, reason = requested, False, None
    api = {"api_status": "not_called", "token_usage": None, "cost": None}
    evidence = []
    if requested == "SEMANTIC_FORMAL":
        try:
            evidence, api = extractor(repo_root, case["problem_id"], case["text"], model, reasoning_effort)
        except SemanticExtractionError as exc:
            api, reason = exc.metadata, str(exc)
            effective, fallback = "FORMAL_OFFLINE", True
        except Exception as exc:
            api, reason = {"api_status": "extraction_error", "token_usage": None, "cost": None}, type(exc).__name__
            effective, fallback = "FORMAL_OFFLINE", True
    try:
        result = evaluator(repo_root, output_dir / effective.lower(), case["problem_id"],
                           case["text"], effective, evidence)
    except Exception as exc:
        technical = f"evaluation_error:{type(exc).__name__}"
        if effective == "SEMANTIC_FORMAL":
            effective, fallback, reason = "FORMAL_OFFLINE", True, technical
            try:
                result = evaluator(repo_root, output_dir / "formal_offline", case["problem_id"],
                                   case["text"], effective, ())
                result.setdefault("technical_errors", []).append(technical)
            except Exception as fallback_exc:
                result = terminal_error(repo_root, case["problem_id"], technical + ";fallback_error:" + type(fallback_exc).__name__)
        else:
            result = terminal_error(repo_root, case["problem_id"], technical)
    result.update(solution_id=case["solution_id"], problem_id=case["problem_id"],
        mode_requested=requested, mode_effective=effective, fallback_used=fallback,
        fallback_reason=reason, api_status=api.get("api_status"), api=api,
        token_usage=api.get("token_usage"), cost=api.get("cost"),
        latency_seconds=time.perf_counter() - start,
        model_configuration={"model": model, "reasoning_effort": reasoning_effort})
    result["award_policy"] = AWARD_POLICY
    result["structural_metrics"] = case_metrics(result)
    return result


def terminal_error(repo_root, problem_id, reason):
    """Last-resort numeric result, explicitly marked unusable as a clean comparison."""
    assets = validate_problem_assets(repo_root / "problems" / problem_id, problem_id)
    rubric, decisions = formal_award_gate(problem_id, [], [], rubric_config=assets.rubric)
    return {"award_policy": AWARD_POLICY, "score": rubric.score,
        "rubric_items": [i.model_dump(mode="json") for i in rubric.items],
        "extracted_evidence": [], "student_claim_checks": [],
        "formal_award_decisions": decisions,
        "lean_status": "technical_error", "lean": {"certificate": {"status": "error"}},
        "technical_errors": [reason]}
