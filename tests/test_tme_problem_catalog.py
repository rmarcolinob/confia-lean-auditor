"""Official statements are content, never an alternate source of scoring rules."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from confia_lean_auditor.core.problem_catalog import (
    CATALOG, ProblemCatalogError, list_problem_catalog, list_tme_problem_catalog,
)
from confia_lean_auditor.tme.audit_models import PUBLIC_PROBLEMS
from confia_lean_auditor.tme.registry import TME_PROBLEMS
from test_tme_pilot import setup

ROOT = Path(__file__).resolve().parents[1]
IDS = [f"TME2026P{n}" for n in range(1, 6)]


def test_exact_content_auditor_pauta_correspondence():
    catalog = list_tme_problem_catalog(ROOT)
    assert [p["problem_id"] for p in catalog] == IDS == list(PUBLIC_PROBLEMS)
    assert set(PUBLIC_PROBLEMS.values()) == set(TME_PROBLEMS)
    for n, p in enumerate(catalog, 1):
        assert p["id"] == p["problem_id"]
        assert p["title"] == f"TME² 2026 — Problema {n}"
        assert p["max_score"] == 20 and p["statement"].strip()
        assert p["pauta_reference"] == f"examples/pautas/tme2_problem{n}.v1.json"
        items = [b for b in p["statement_blocks"] if b.get("item_id")]
        assert [b["item_id"] for b in items] == list("abcd" if n in (1, 5) else "abc")
        assert all(b["text"].startswith(f'({b["item_id"]}) ') for b in items)
        assert p["source"]["document"] == "Segunda Fase TME² - Gabarito com pauta.pdf"
        assert p["source"]["sha256"] == "a2660f1c0761738a8b9232dc179feaea9538efb45102e1b2a9b991a3dd2ac384"


@pytest.mark.parametrize("n,forbidden", [
    (1, ["731−137=594", "731 - 137 = 594", "99,198,297", "30 números"]),
    (2, ["384", "(1,12)", "(1, 12)", "45+3", "4!"]),
    (3, ["11/36", r"\frac{11}{36}", "A melhor estratégia", "1/6"]),
    (4, ["13/3", r"\frac{13}{3}", "=12", "= 12", "=18", "= 18"]),
    (5, ["54", "674", "675", "676", "melhor lista"]),
])
def test_statement_excludes_solutions_and_pauta(n, forbidden):
    p = list_tme_problem_catalog(ROOT)[n - 1]
    displayed = p["statement"] + " ".join(f["alt"] for f in p["figures"])
    for value in forbidden + ["Pauta de Correção", "Orientação geral", "pontos:", "Resolução"]:
        assert value not in displayed
    # Schema has no correct_answer, scoring rules, or solution content.
    assert not {"correct_answer", "solution", "obligations", "rubric"} & p.keys()


def test_complete_context_not_just_item_questions():
    p1, p2, p3, p4, p5 = list_tme_problem_catalog(ROOT)
    assert r"\overline{abc} = 100a + 10b + c" in p1["statement"]
    assert "804 - 408 = 396" in p1["statement"]  # Official example, not a solution.
    assert "Dois preenchimentos são considerados diferentes" in p2["statement"]
    assert "demais bolas desse compartimento descem uma posição" in p3["statement"]
    assert "Considerando o jogo desde o primeiro acionamento" in p3["statement"]
    assert r"\(PB = x\)" in p4["statement"]
    assert "Na etapa final do desafio, o professor anunciou o número 2026." in p5["statement"]
    assert "A ordem em que os números são escritos não importa." in p5["statement"]


@pytest.mark.parametrize("n,count", [(1, 0), (2, 2), (3, 1), (4, 1), (5, 0)])
def test_api_lists_and_opens_every_problem_with_original_figures(setup, n, count):
    client, calls, _ = setup
    response = client.get("/tme/problems")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    catalog = response.json()
    assert [p["problem_id"] for p in catalog if p["problem_id"].startswith("TME")] == IDS
    # Existing ITA response entries are preserved byte-for-byte as JSON values.
    assert [p for p in catalog if p["problem_id"] in CATALOG] == list_problem_catalog(ROOT)
    p = next(p for p in catalog if p["problem_id"] == IDS[n - 1])
    assert p == list_tme_problem_catalog(ROOT)[n - 1]
    assert len(p["figures"]) == count
    for figure in p["figures"]:
        asset = client.get(figure["src"])
        assert asset.status_code == 200
        assert asset.headers["content-type"] == "image/png"
        assert hashlib.sha256(asset.content).hexdigest() == figure["sha256"]
    case = client.post("/tme/cases", json=dict(problem_id=p["problem_id"],
        external_candidate_ref="CATALOG-CONTROL", source_mode="IMAGE_SCAN"))
    assert case.status_code == 201
    case_id = case.json()["case_id"]
    assert client.get(f"/tme/cases/{case_id}").json()["problem_id"] == p["problem_id"]
    assert client.get(f"/tme?case_id={case_id}").status_code == 200
    assert calls == []  # Viewing catalog/figures never runs an auditor or OCR.


@pytest.fixture
def content_copy(tmp_path):
    for pid in IDS:
        shutil.copytree(ROOT / "problems" / pid, tmp_path / "problems" / pid)
    for relative in ("examples/pautas", "app/confia_lean_auditor/static/problem-assets"):
        shutil.copytree(ROOT / relative, tmp_path / relative)
    return tmp_path


@pytest.mark.parametrize("mutation", ["missing", "extra", "id", "pauta", "item", "asset", "figure_ref", "blank", "solution"])
def test_catalog_rejects_incomplete_or_mismatched_content(content_copy, mutation):
    path = content_copy / "problems/TME2026P2/problem.json"
    data = json.loads(path.read_text())
    if mutation == "missing":
        path.unlink()
    elif mutation == "extra":
        shutil.copytree(path.parent, path.parent.with_name("TME2026P6"))
    else:
        if mutation == "id": data["problem_id"] = "TME2026P3"
        if mutation == "pauta": data["pauta_reference"] = "examples/pautas/tme2_problem3.v1.json"
        if mutation == "item": data["statement_blocks"] = [b for b in data["statement_blocks"] if b.get("item_id") != "c"]
        if mutation == "asset": data["figures"][0]["src"] = "/static/problem-assets/TME2026P2/missing.png"
        if mutation == "figure_ref": data["statement_blocks"][1]["figure_id"] = "wrong"
        if mutation == "blank": data["statement_blocks"][0]["text"] = "  "
        if mutation == "solution": data["solution"] = "Forbidden extra content"
        path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        list_tme_problem_catalog(content_copy)


def test_auditor_without_public_content_alias_is_rejected(monkeypatch):
    from confia_lean_auditor.tme import registry
    monkeypatch.setattr(registry, "TME_PROBLEMS", {**TME_PROBLEMS, "TME2026P6": "unused.json"})
    with pytest.raises(ProblemCatalogError, match="registries"):
        list_tme_problem_catalog(ROOT)
