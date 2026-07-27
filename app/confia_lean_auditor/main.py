from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException

from confia_lean_auditor.claims.extract_claims import extract_claims
from confia_lean_auditor.core.paths import InvalidProblemId, get_problem_dir, get_repo_root
from confia_lean_auditor.core.problem_assets import ProblemAssetValidationError, validate_problem_assets
from confia_lean_auditor.core.schemas import AuditRequest, AuditResponse, LeanCertificate
from confia_lean_auditor.lean.build_attempt import build_attempt
from confia_lean_auditor.lean.formal_step_evaluator import evaluate_formal_steps
from confia_lean_auditor.lean.microclaim_evaluator import evaluate_microclaims
from confia_lean_auditor.lean.run_lean import run_lean_file
from confia_lean_auditor.reports.report_builder import build_feedback, verdict_from_score
from confia_lean_auditor.rubric.rubric_evaluator import evaluate_rubric, apply_student_claim_adjustments
from confia_lean_auditor.llm.formal_step_extractor import FormalStepExtractionError
from confia_lean_auditor.student_claims.extract_f2q8_student_claims import extract_f2q8_student_claims
from confia_lean_auditor.lean.student_claim_checker import check_student_claims


app = FastAPI(title="ConfIA Lean Auditor", version="0.4.0")


def repo_root() -> Path:
    return get_repo_root()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ConfIA Lean Auditor",
        "version": "0.4.0"
    }


@app.post("/audit", response_model=AuditResponse)
def audit(req: AuditRequest) -> AuditResponse:
    root = repo_root()

    try:
        problem_dir = get_problem_dir(root, req.problem_id)
    except InvalidProblemId as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not problem_dir.exists():
        raise HTTPException(status_code=404, detail="Problem not found: " + req.problem_id)

    try:
        assets = validate_problem_assets(problem_dir, req.problem_id)
    except ProblemAssetValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    artifact_dir = root / "artifacts" / "runs" / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    try:
        claim_extraction = extract_claims(req.problem_id, req.solution)
    except FormalStepExtractionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        formal_steps = evaluate_formal_steps(
            repo_root=root,
            problem_id=req.problem_id,
            claim_extraction=claim_extraction,
            artifact_dir=artifact_dir,
        )
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    try:
        attempt_build = build_attempt(
            repo_root=root,
            problem_id=req.problem_id,
            claim_extraction=claim_extraction,
            artifact_dir=artifact_dir,
            formal_step_results=formal_steps,
        )
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    attempt_path = attempt_build["attempt_path"]
    generated_theorems = attempt_build["generated_theorems"]

    lean_raw = run_lean_file(root, attempt_path)
    lean_raw["lean_file"] = str(attempt_path)
    lean_raw["generated_theorems"] = generated_theorems

    lean_certificate = LeanCertificate(**lean_raw)

    try:
        microclaims = evaluate_microclaims(
            repo_root=root,
            problem_id=req.problem_id,
            claim_extraction=claim_extraction,
            lean_certificate=lean_certificate,
            generated_theorems=generated_theorems,
            formal_step_results=formal_steps,
            microclaims_config=assets.microclaims,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


    student_claims = []
    student_claim_checks = []

    if req.problem_id == "ITA2025F2Q8":
        student_claims = extract_f2q8_student_claims(req.solution)
        student_claim_checks = check_student_claims(
            student_claims,
            run_id=f"{run_id}_student_claims",
        )

    student_claims_payload = [asdict(claim) for claim in student_claims]
    student_claim_checks_payload = [asdict(check) for check in student_claim_checks]

    try:
        rubric = evaluate_rubric(
            repo_root=root,
            problem_id=req.problem_id,
            claim_extraction=claim_extraction,
            microclaims=microclaims,
            rubric_config=assets.rubric,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    rubric = apply_student_claim_adjustments(
        rubric=rubric,
        problem_id=req.problem_id,
        student_claim_checks=student_claim_checks_payload,
    )

    verdict = verdict_from_score(rubric.score, rubric.max_score)
    feedback = build_feedback(rubric, lean_certificate, microclaims)


    response = AuditResponse(
        problem_id=req.problem_id,
        score=rubric.score,
        max_score=rubric.max_score,
        verdict=verdict,
        extracted_claims=claim_extraction,
        formal_steps=formal_steps,
        rubric_assessment=rubric,
        lean_certificate=lean_certificate,
        microclaims=microclaims,
        student_claims=student_claims_payload,
        student_claim_checks=student_claim_checks_payload,
        feedback=feedback,
        artifact_dir=str(artifact_dir),
    )

    (artifact_dir / "audit.json").write_text(
        json.dumps(response.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (artifact_dir / "solution.txt").write_text(req.solution, encoding="utf-8")
    (artifact_dir / "claims.json").write_text(
        json.dumps(claim_extraction.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (artifact_dir / "student_claims.json").write_text(
        json.dumps(student_claims_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (artifact_dir / "student_claim_checks.json").write_text(
        json.dumps(student_claim_checks_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return response
