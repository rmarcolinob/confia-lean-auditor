"""The accepted HMER source and typed text use the same F2Q3 audit extractors."""

import json
from pathlib import Path

from fastapi.testclient import TestClient
import httpx

import confia_lean_auditor.main as main
from confia_lean_auditor.claims.extract_claims import extract_claims
from confia_lean_auditor.core.audit_math_projection import project_audit_math
from confia_lean_auditor.core.schemas import FormalStepResult, LeanCertificate
from confia_lean_auditor.lean.microclaim_evaluator import evaluate_microclaims
from confia_lean_auditor.recognition.mathpix import MathpixRecognitionProvider
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.rubric.rubric_evaluator import evaluate_rubric
from confia_lean_auditor.student_claims.registry import extract_student_claims
from confia_lean_auditor.submissions import router as submissions
from test_submission_audits import result
from test_submissions import payload


PROBLEM = "ITA2025F2Q3"
PLAIN = ("Como sen alpha - sen beta = 1/4 e sen alpha - 2 sen beta + cos beta = 3/4, "
         "então 1/4 - sen beta + cos beta = 3/4, ou seja, cos beta - sen beta = 1/2. "
         "Mas sen(alpha+beta)=sen alpha cos beta + sen beta cos alpha.")
LATEX = (r"\[\begin{array}{l}"
         r"\operatorname{sen}\alpha-\operatorname{sen}\beta=\frac{1}{4}\\"
         r"\operatorname{sen}\alpha-2\operatorname{sen}\beta+\cos\beta=\frac{3}{4}\\"
         r"\frac{1}{4}-\operatorname{sen}\beta+\cos\beta=\frac{3}{4}\\"
         r"\cos\beta-\operatorname{sen}\beta=\frac{1}{2}\\"
         r"\operatorname{sen}(\alpha+\beta)=\operatorname{sen}\alpha\cdot\cos\beta"
         r"+\operatorname{sen}\beta\cdot\cos\alpha\end{array}\]")


def types(solution):
    extracted = extract_claims(PROBLEM, solution)
    student = extract_student_claims(PROBLEM, solution)
    return ([item.type for item in extracted.claims],
            [item.type for item in extracted.formal_steps],
            [(item.claim_type, item.data) for item in student])


def test_plain_and_mathpix_syntax_have_the_same_relevant_claims():
    plain = types(PLAIN)
    assert types(LATEX) == plain
    assert plain[0] == ["beta_difference", "sin_sum_identity"]
    assert plain[1] == ["f2q3_beta_difference"]
    assert [item[0] for item in plain[2]] == ["f2q3_student_beta_difference"]
    assert "candidate_values" not in plain[0]
    assert "final_sin_sum" not in plain[0]
    assert "final_answer" not in plain[0]


def test_projection_preserves_falsehoods_signs_and_general_fractions():
    assert project_audit_math(r"\frac{a}{b}") == "a/b"
    assert project_audit_math(r"\frac{5+\sqrt{7}}{8}") == "(5+sqrt(7))/8"
    assert project_audit_math(r"\cos\beta-\operatorname{sen}\beta=-\frac{1}{2}") == "cosbeta-senbeta=-1/2"
    assert project_audit_math("2+2=5") == "2+2=5"
    wrong = LATEX.replace(r"=\frac{1}{2}\\", r"=-\frac{1}{2}\\")
    assert "beta_difference" not in types(wrong)[0]
    assert types(wrong)[2] == [("f2q3_student_beta_difference", {"value_expr": "-1 / 2"})]
    assert "beta_difference" not in types("Subtraindo, cos beta - sen beta = -1/2")[0]
    direct = types("sen(alpha+beta)=(5+sqrt(7))/8")
    assert [item[0] for item in direct[2]] == ["f2q3_student_final_sin_sum", "f2q3_student_final_answer"]


def test_lean_timeout_keeps_textual_claim_and_never_awards_or_zeros_without_proof():
    claims = extract_claims(PROBLEM, LATEX)
    certificate = LeanCertificate(status="lean_timeout", compiled=False, exit_code=124,
                                  uses_forbidden_token=False, forbidden_tokens_found=[])
    step = FormalStepResult(**claims.formal_steps[0].model_dump(), lean_file="Attempt.lean",
                            status="lean_timeout", compiled=False, exit_code=124)
    root = Path(__file__).resolve().parents[1]
    microclaims = evaluate_microclaims(root, PROBLEM, claims, certificate, [], [step])
    beta = next(item for item in microclaims if item.id == "f2q3_beta_difference")
    assert beta.textual_evidence is True
    assert beta.verification_status == "technical_error"
    rubric = evaluate_rubric(root, PROBLEM, claims, microclaims)
    criterion = next(item for item in rubric.items if item.id == "beta_difference")
    assert criterion.points is None and criterion.verification_status == "technical_error"


def test_accepted_automatic_revision_reaches_same_engine_without_mutation(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(tmp_path / "audits"))
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "test-id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "test-key")
    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: MathpixRecognitionProvider(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json={"latex_styled": LATEX}))))
    monkeypatch.setattr(submissions, "configured_registry", lambda: registry)
    requests = []

    def engine(request):
        requests.append(request)
        return result(request.problem_id)

    monkeypatch.setattr(main, "execute_audit", engine)
    client = TestClient(main.app)
    body = payload()
    snapshot = json.loads(body["snapshot_json"])
    snapshot["problem_id"] = PROBLEM
    body["snapshot_json"] = json.dumps(snapshot)
    sid = client.post("/submissions", json=body).json()["submission_id"]
    summary = client.post(f"/submissions/{sid}/recognitions", json={"provider": "mathpix"}).json()
    tid = summary["transcription_id"]
    revision = client.get(f"/transcriptions/{tid}").json()["revisions"][0]
    assert revision["status"] == "NEEDS_REVIEW" and revision["segments"][0]["latex"] == LATEX
    before = (tmp_path / "submissions" / sid / "transcriptions" / tid / "revisions" / "revision_000001.json").read_bytes()
    acceptance = client.post(f"/transcriptions/{tid}/accept", json={
        "revision_number": 1, "reviewer_reference": "professor-teste-01"}).json()["acceptance"]
    response = client.post(f"/submissions/{sid}/audits", json={
        "transcription_id": tid, "revision_number": 1, "acceptance_id": acceptance["acceptance_id"]})
    assert response.status_code == 200, response.text
    assert requests[0].solution == LATEX
    assert types(requests[0].solution) == types(PLAIN)
    assert response.json()["source"]["solution_text"] == LATEX
    assert (tmp_path / "submissions" / sid / "transcriptions" / tid / "revisions" / "revision_000001.json").read_bytes() == before
