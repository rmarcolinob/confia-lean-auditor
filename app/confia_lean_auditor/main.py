from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException

from confia_lean_auditor.claims.extract_claims import extract_claims
from confia_lean_auditor.core.schemas import AuditRequest, AuditResponse, LeanCertificate
from confia_lean_auditor.lean.microclaim_evaluator import evaluate_microclaims
from confia_lean_auditor.lean.run_lean import run_problem
from confia_lean_auditor.reports.report_builder import build_feedback, verdict_from_score
from confia_lean_auditor.rubric.rubric_evaluator import evaluate_rubric


app = FastAPI(title="ConfIA Lean Auditor", version="0.2.0")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ConfIA Lean Auditor",
        "version": "0.2.0"
    }


@app.post("/audit", response_model=AuditResponse)
def audit(req: AuditRequest) -> AuditResponse:
    root = repo_root()
    problem_dir = root / "problems" / req.problem_id

    if not problem_dir.exists():
        raise HTTPException(status_code=404, detail="Problem not found: " + req.problem_id)

    claim_extraction = extract_claims(req.problem_id, req.solution)

    try:
        rubric = evaluate_rubric(root, req.problem_id, claim_extraction)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    lean_raw = run_problem(root, req.problem_id)
    lean_certificate = LeanCertificate(**lean_raw)

    microclaims = evaluate_microclaims(
        repo_root=root,
        problem_id=req.problem_id,
        claim_extraction=claim_extraction,
        lean_certificate=lean_certificate,
    )

    verdict = verdict_from_score(rubric.score, rubric.max_score)
    feedback = build_feedback(rubric, lean_certificate, microclaims)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    artifact_dir = root / "artifacts" / "runs" / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    response = AuditResponse(
        problem_id=req.problem_id,
        score=rubric.score,
        max_score=rubric.max_score,
        verdict=verdict,
        extracted_claims=claim_extraction,
        rubric_assessment=rubric,
        lean_certificate=lean_certificate,
        microclaims=microclaims,
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

    return response
