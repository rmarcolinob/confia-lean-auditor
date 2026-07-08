import json
from pathlib import Path


PROBLEMS_DIR = Path("problems")

EXTRACT_CLAIMS = Path("app/confia_lean_auditor/claims/extract_claims.py")
BUILD_ATTEMPT = Path("app/confia_lean_auditor/lean/build_attempt.py")
FORMAL_STEP_EVALUATOR = Path("app/confia_lean_auditor/lean/formal_step_evaluator.py")


def implemented_problem_ids():
    ids = []
    for problem_json in sorted(PROBLEMS_DIR.glob("ITA2025*/problem.json")):
        data = json.loads(problem_json.read_text(encoding="utf-8"))
        ids.append(data["id"])
    return ids


def problem_uses_formal_steps(problem_id: str) -> bool:
    microclaims_path = PROBLEMS_DIR / problem_id / "microclaims.json"
    if not microclaims_path.exists():
        return False

    data = json.loads(microclaims_path.read_text(encoding="utf-8"))

    for item in data.get("microclaims", []):
        if item.get("required_formal_step_types"):
            return True

    return False


def test_all_implemented_problems_have_claim_extractors():
    text = EXTRACT_CLAIMS.read_text(encoding="utf-8")

    for problem_id in implemented_problem_ids():
        assert f'problem_id == "{problem_id}"' in text, (
            f"{problem_id} is missing from claims/extract_claims.py"
        )


def test_all_implemented_problems_have_attempt_builders():
    text = BUILD_ATTEMPT.read_text(encoding="utf-8")

    for problem_id in implemented_problem_ids():
        assert f'problem_id == "{problem_id}"' in text, (
            f"{problem_id} is missing from lean/build_attempt.py"
        )


def test_problems_with_formal_steps_have_formal_step_renderer_routes():
    text = FORMAL_STEP_EVALUATOR.read_text(encoding="utf-8")

    for problem_id in implemented_problem_ids():
        if problem_uses_formal_steps(problem_id):
            assert f'problem_id == "{problem_id}"' in text, (
                f"{problem_id} uses formal steps but is missing from formal_step_evaluator.py"
            )
