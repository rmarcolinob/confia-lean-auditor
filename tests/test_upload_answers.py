"""Upload -> GLM-OCR -> student answer only. Hermetic: no Ollama, Lean or network."""
import base64
import io
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from confia_lean_auditor.main import app
from confia_lean_auditor.recognition.glm_ocr import GlmOcrClient, GlmOcrError, GlmOcrPage, PROMPT
from confia_lean_auditor.uploads import service
from confia_lean_auditor.uploads.answer_extraction import extract_answer

PROBLEM = "ITA2025F2Q1"
STATEMENT = ("Encontre os valores reais a e b tais que o polinômio p(x)=x^57+a x^14+b x^7+1, "
             "ao ser dividido por x^2-x+1, deixe resto 2x+1.")
# A GLM-OCR page: header, statement in LaTeX and the handwritten answer.
OCR_PAGE = "\n".join([
    "ITA 2025 - 2ª fase - Matemática",
    "Questão 1",
    "Encontre os valores reais $a$ e $b$ tais que o polinômio $p(x)=x^{57}+a x^{14}+b x^{7}+1$,",
    "ao ser dividido por $x^{2}-x+1$, deixe resto $2x+1$.",
    "Seja $\\omega$ raiz de $x^2-x+1$, então $\\omega^3=-1$.",
    "$p(\\omega) = -\\omega^{2}\\cdot a + \\ldots$",
    "Logo $a = 3$ e $b = -2$.",
])


def png_bytes(size=(40, 30)):
    from PIL import Image
    out = io.BytesIO()
    Image.new("RGB", size, "white").save(out, format="PNG")
    return out.getvalue()


def pdf_bytes(pages=1):
    import pypdfium2 as pdfium
    document = pdfium.PdfDocument.new()
    for _ in range(pages):
        document.new_page(595, 842)
    out = io.BytesIO()
    document.save(out)
    return out.getvalue()


def body(*files, problem_id=PROBLEM):
    return {"problem_id": problem_id,
            "files": [{"filename": f"f{i}", "data_base64": base64.b64encode(f).decode()} for i, f in enumerate(files)]}


class FakeGlm:
    base_url = "http://ollama.invalid"
    adapter, adapter_version = "confia_glm_ocr_ollama", "1.0.0"
    public_parameters = {"model": "glm-ocr", "prompt": PROMPT, "temperature": 0}

    def __init__(self, pages):
        self.pages, self.calls = list(pages), []

    def transcribe(self, png, deadline=None):
        self.calls.append(png)
        return GlmOcrPage(text=self.pages[len(self.calls) - 1], latency_ms=5.0, output_tokens=40, truncated=False)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "0")
    return TestClient(app)


@pytest.fixture
def fake_glm(monkeypatch):
    def install(*pages):
        fake = FakeGlm(pages)
        monkeypatch.setattr(service, "GlmOcrClient", lambda: fake)
        return fake
    return install



def test_statement_and_header_are_removed_and_kept_for_review():
    result = extract_answer([OCR_PAGE], STATEMENT)
    assert result.statement_found and result.statement_match >= 0.75
    assert result.answer_text.startswith("Seja $\\omega$")
    assert result.answer_text.endswith("Logo $a = 3$ e $b = -2$.")
    assert "Encontre os valores" not in result.answer_text
    kinds = [b.kind for b in result.removed]
    assert kinds == ["before_statement", "statement"]
    assert "Questão 1" in result.removed[0].text


def test_missing_statement_returns_everything_with_warning():
    result = extract_answer(["x = 7", "logo a área é 20"], STATEMENT)
    assert not result.statement_found
    assert result.answer_text == "x = 7\n\nlogo a área é 20"
    assert result.warnings[0].startswith("STATEMENT_NOT_FOUND")


def test_answer_continues_on_following_pages():
    result = extract_answer([OCR_PAGE, "Verificação: p(1) = 3"], STATEMENT)
    assert result.answer_text.endswith("Verificação: p(1) = 3")
    assert result.pages[1].answer_text == "Verificação: p(1) = 3"



def test_upload_png_returns_only_student_answer(client, fake_glm):
    fake = fake_glm(OCR_PAGE)
    response = client.post("/uploads/answers", json=body(png_bytes()))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "NEEDS_REVIEW" and data["statement_found"] is True
    assert data["answer_text"].startswith("Seja $\\omega$") and "Encontre" not in data["answer_text"]
    assert data["pages"][0]["source_media_type"] == "image/png"
    assert data["upload_id"].startswith("upl_") and response.headers["cache-control"] == "no-store"
    assert len(fake.calls) == 1 and fake.calls[0].startswith(b"\x89PNG")


def test_large_photo_is_reduced_before_ocr(client, fake_glm):
    fake = fake_glm(OCR_PAGE)
    data = client.post("/uploads/answers", json=body(png_bytes((4000, 3000)))).json()
    assert max(data["pages"][0]["width"], data["pages"][0]["height"]) == 1600
    assert len(fake.calls) == 1


def test_pdf_pages_are_rendered_in_order(client, fake_glm):
    fake = fake_glm(OCR_PAGE, "answer continues")
    data = client.post("/uploads/answers", json=body(pdf_bytes(2))).json()
    assert [p["page_in_source"] for p in data["pages"]] == [0, 1]
    assert data["answer_text"].endswith("answer continues")
    assert len(fake.calls) == 2


@pytest.mark.parametrize("payload, status", [
    (lambda: body(b"GIF89a....."), 415),
    (lambda: body(png_bytes(), problem_id="NAO_EXISTE"), 422),
    (lambda: body(pdf_bytes(4)), 422),
    (lambda: {"problem_id": PROBLEM, "files": [{"data_base64": "%%%"}]}, 422),
])
def test_invalid_uploads_are_rejected_before_ocr(client, fake_glm, payload, status):
    fake = fake_glm(OCR_PAGE)
    response = client.post("/uploads/answers", json=payload())
    assert response.status_code == status
    assert fake.calls == []


def test_not_configured_is_503(client, monkeypatch):
    monkeypatch.delenv("CONFIA_GLM_OCR_URL", raising=False)
    response = client.post("/uploads/answers", json=body(png_bytes()))
    assert response.status_code == 503 and response.json()["detail"] == "PROVIDER_NOT_CONFIGURED"


def test_status_reports_configuration(client, monkeypatch):
    monkeypatch.setenv("CONFIA_GLM_OCR_URL", "http://localhost:11434")
    assert client.get("/uploads/status").json()["configured"] is True



def test_audit_route_sends_answer_to_the_existing_engine(client, fake_glm, monkeypatch):
    fake_glm(OCR_PAGE)
    received = []

    def engine(request):
        received.append(request)
        raise NotImplementedError()

    monkeypatch.setattr("confia_lean_auditor.main.execute_audit", engine)
    data = client.post("/uploads/audits", json=body(png_bytes())).json()
    assert received[0].problem_id == PROBLEM
    assert received[0].solution == data["ocr"]["answer_text"]
    assert data["audit"] is None and data["audit_error"]["status"] == 501
    assert data["warnings"][0].startswith("AUTOMATIC_AUDIT_OF_UNREVIEWED_OCR")


def test_audit_route_skips_engine_when_answer_is_empty(client, fake_glm, monkeypatch):
    fake_glm("Encontre os valores reais a e b tais que o polinômio p(x)=x^57+a x^14+b x^7+1, "
             "ao ser dividido por x^2-x+1, deixe resto 2x+1.")
    monkeypatch.setattr("confia_lean_auditor.main.execute_audit", lambda r: pytest.fail("engine must not run"))
    data = client.post("/uploads/audits", json=body(png_bytes())).json()
    assert data["audit_error"]["error_code"] == "EMPTY_ANSWER"



def test_glm_client_calls_ollama_with_official_prompt():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"response": " texto lido ", "eval_count": 12, "done_reason": "stop"})

    client = GlmOcrClient(base_url="http://ollama.test", transport=httpx.MockTransport(handler))
    page = client.transcribe(b"\x89PNGfake")
    assert page.text == "texto lido" and page.output_tokens == 12 and not page.truncated
    assert seen["model"] == "glm-ocr" and seen["prompt"] == PROMPT and seen["options"]["temperature"] == 0
    assert base64.b64decode(seen["images"][0]) == b"\x89PNGfake"


def test_glm_client_flags_truncation_and_hides_http_errors():
    long = GlmOcrClient(base_url="http://t", transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={"response": "100\n" * 50, "done_reason": "length"})))
    assert long.transcribe(b"x").truncated
    failing = GlmOcrClient(base_url="http://t", transport=httpx.MockTransport(
        lambda r: httpx.Response(500, text="server secret")))
    with pytest.raises(GlmOcrError) as info:
        failing.transcribe(b"x")
    assert str(info.value) == "http_5xx"
