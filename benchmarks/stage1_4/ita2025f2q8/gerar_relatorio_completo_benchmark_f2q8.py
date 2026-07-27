from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


ROOT = Path(__file__).resolve().parents[3]
BENCH_DIR = ROOT / "benchmarks" / "stage1_4" / "ita2025f2q8"

DEFAULT_GOLD = BENCH_DIR / "gold_100.csv"
DEFAULT_REPORT = BENCH_DIR / "reports" / "stage1_4_f2q8_report_100_v2.json"
DEFAULT_OUT_MD = BENCH_DIR / "reports" / "relatorio_completo_benchmark_f2q8_stage1_4.md"
DEFAULT_OUT_CSV = BENCH_DIR / "reports" / "tabela_completa_benchmark_f2q8_stage1_4.csv"
DEFAULT_OUT_JSON = BENCH_DIR / "reports" / "relatorio_completo_benchmark_f2q8_stage1_4.json"


CLAIM_LABELS = {
    "matrix_transformation": "Transformação por diferenças sucessivas de colunas",
    "determinant_formula": "Fórmula geral det(A_k)=(-1)^(k-1)k",
    "alternating_sum": "Redução à soma alternada 1-2+3-4+...+2025",
    "final_answer": "Resposta final 1013",
}

STEP_LABELS = {
    "f2q8_bridge": "Ponte formal: maxMatrix * colDiffMatrix = transformedShape",
    "f2q8_coldiff_det_one": "Matriz de diferenças tem determinante 1",
    "f2q8_determinant_formula": "Teorema formal da fórmula geral do determinante",
    "f2q8_final_sum": "Verificação formal da soma final até 2025",
}

CATEGORY_LABELS = {
    "A": "Correta",
    "B": "Erro de conta",
    "C": "Erro de conceito",
    "D": "Parcial",
    "E": "Formato difícil",
    "F": "Adversarial",
}


def parse_set(value: str | Iterable[str] | None) -> Set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return set()
        return {x.strip() for x in value.split("|") if x.strip()}
    return {str(x).strip() for x in value if str(x).strip()}


def render_set(items: Iterable[str], labels: Dict[str, str] | None = None) -> str:
    labels = labels or {}
    items = sorted(set(items))
    if not items:
        return "∅"
    return "; ".join(labels.get(x, x) for x in items)


def status(expected: Set[str], got: Set[str]) -> str:
    missing = expected - got
    extra = got - expected
    if not missing and not extra:
        return "OK"
    if missing and extra:
        return "FALTOU_E_EXTRAIU_A_MAIS"
    if missing:
        return "FALTOU"
    return "EXTRAIU_A_MAIS"


def infer_what_solution_says(row: Dict[str, str]) -> str:
    expected_claims = parse_set(row.get("expected_claims", ""))
    category = row.get("category", "")

    parts: List[str] = []
    if "matrix_transformation" in expected_claims:
        parts.append("menciona transformação por diferenças de colunas")
    if "determinant_formula" in expected_claims:
        parts.append("afirma/usa a fórmula correta do determinante")
    if "alternating_sum" in expected_claims:
        parts.append("reduz a expressão a uma soma alternada")
    if "final_answer" in expected_claims:
        parts.append("apresenta 1013 como resposta final")

    if not parts:
        if category == "F":
            return "não contém conteúdo matemático suficiente para claims da F2Q8"
        return "não contém claims esperados da F2Q8 segundo a anotação gold"

    prefix = CATEGORY_LABELS.get(category, category)
    return f"{prefix}: " + "; ".join(parts) + "."


def load_gold(path: Path) -> Dict[str, Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {row["id"]: row for row in rows}


def load_report(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_complete_rows(gold: Dict[str, Dict[str, str]], report: Dict[str, Any]) -> List[Dict[str, Any]]:
    report_rows = {row["id"]: row for row in report["rows"]}
    all_ids = sorted(set(gold) | set(report_rows))

    complete: List[Dict[str, Any]] = []
    for row_id in all_ids:
        g = gold.get(row_id, {})
        r = report_rows.get(row_id, {})

        expected_claims = parse_set(g.get("expected_claims", r.get("expected_claims", [])))
        expected_steps = parse_set(g.get("expected_formal_steps", r.get("expected_formal_steps", [])))
        got_claims = parse_set(r.get("got_claims", []))
        got_steps = parse_set(r.get("got_formal_steps", []))

        complete.append(
            {
                "id": row_id,
                "problem_id": g.get("problem_id", "ITA2025F2Q8"),
                "category": g.get("category", r.get("category", "")),
                "category_label": CATEGORY_LABELS.get(
                    g.get("category", r.get("category", "")),
                    g.get("category", r.get("category", "")),
                ),
                "solution": g.get("solution", ""),
                "what_solution_really_says": infer_what_solution_says(g),
                "stage_1_input_valid": r.get("input_valid"),
                "stage_2_load_success": r.get("load_success"),
                "expected_claims": sorted(expected_claims),
                "got_claims": sorted(got_claims),
                "missing_claims": sorted(expected_claims - got_claims),
                "extra_claims": sorted(got_claims - expected_claims),
                "claim_status": status(expected_claims, got_claims),
                "expected_formal_steps": sorted(expected_steps),
                "got_formal_steps": sorted(got_steps),
                "missing_formal_steps": sorted(expected_steps - got_steps),
                "extra_formal_steps": sorted(got_steps - expected_steps),
                "formal_step_status": status(expected_steps, got_steps),
                "claim_precision_row": r.get("claim_metrics", {}).get("precision"),
                "claim_recall_row": r.get("claim_metrics", {}).get("recall"),
                "claim_f1_row": r.get("claim_metrics", {}).get("f1"),
                "formal_step_precision_row": r.get("formal_step_metrics", {}).get("precision"),
                "formal_step_recall_row": r.get("formal_step_metrics", {}).get("recall"),
                "formal_step_f1_row": r.get("formal_step_metrics", {}).get("f1"),
                "extraction_error": r.get("extraction_error"),
            }
        )

    return complete


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "id",
        "problem_id",
        "category",
        "category_label",
        "solution",
        "what_solution_really_says",
        "stage_1_input_valid",
        "stage_2_load_success",
        "expected_claims",
        "got_claims",
        "missing_claims",
        "extra_claims",
        "claim_status",
        "expected_formal_steps",
        "got_formal_steps",
        "missing_formal_steps",
        "extra_formal_steps",
        "formal_step_status",
        "claim_precision_row",
        "claim_recall_row",
        "claim_f1_row",
        "formal_step_precision_row",
        "formal_step_recall_row",
        "formal_step_f1_row",
        "extraction_error",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            flat = dict(row)
            for key in [
                "expected_claims",
                "got_claims",
                "missing_claims",
                "extra_claims",
                "expected_formal_steps",
                "got_formal_steps",
                "missing_formal_steps",
                "extra_formal_steps",
            ]:
                flat[key] = "|".join(flat.get(key, []))
            writer.writerow(flat)


def write_json(summary: Dict[str, Any], rows: List[Dict[str, Any]], path: Path) -> None:
    payload = {
        "benchmark": "ITA2025F2Q8 — validação estatística das etapas 1 a 4",
        "description": (
            "Relatório completo com soluções sintéticas geradas, anotação gold, "
            "claims esperados, claims identificados pelo agente, formal_steps esperados "
            "e formal_steps gerados pelo agente."
        ),
        "summary": summary,
        "rows": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def pct(x: Any) -> str:
    if isinstance(x, (int, float)):
        return f"{100*x:.2f}%"
    return str(x)


def write_markdown(summary: Dict[str, Any], rows: List[Dict[str, Any]], path: Path) -> None:
    counts = Counter(row["category"] for row in rows)
    claim_status_counts = Counter(row["claim_status"] for row in rows)
    step_status_counts = Counter(row["formal_step_status"] for row in rows)

    lines: List[str] = []
    lines.append("# Relatório completo do benchmark — ITA2025F2Q8, etapas 1 a 4")
    lines.append("")
    lines.append("## 1. Identificação")
    lines.append("")
    lines.append("- **Problema:** ITA2025F2Q8")
    lines.append("- **Objeto avaliado:** etapas 1 a 4 do ConfIA-auditor")
    lines.append("- **Etapa 1:** entrada `problem_id + solution`")
    lines.append("- **Etapa 2:** carregamento dos assets do problema")
    lines.append("- **Etapa 3:** extração de claims matemáticos")
    lines.append("- **Etapa 4:** geração/mapeamento de `formal_steps`")
    lines.append("- **Observação:** este relatório não mede execução Lean nem nota final; isso pertence às etapas 5 a 8.")
    lines.append("")

    lines.append("## 2. Resumo estatístico")
    lines.append("")
    for key in [
        "n",
        "stage_1_input_valid_rate",
        "stage_2_load_success_rate",
        "stage_3_extraction_success_rate",
        "stage_3_claim_precision",
        "stage_3_claim_recall",
        "stage_3_claim_f1",
        "stage_3_claim_exact_match",
        "stage_4_formal_step_precision",
        "stage_4_formal_step_recall",
        "stage_4_formal_step_f1",
        "stage_4_formal_step_exact_match",
    ]:
        if key in summary:
            value = summary[key]
            if isinstance(value, float):
                lines.append(f"- **{key}:** {value:.6f} ({pct(value)})")
            else:
                lines.append(f"- **{key}:** {value}")
    lines.append("")

    lines.append("## 3. Distribuição das soluções geradas")
    lines.append("")
    for category in sorted(counts):
        label = CATEGORY_LABELS.get(category, category)
        lines.append(f"- **{category} — {label}:** {counts[category]}")
    lines.append("")

    lines.append("## 4. Resultado por categoria")
    lines.append("")
    by_category = summary.get("by_category", {})
    lines.append("| Categoria | n | Claim F1 | Claim exact | Formal step F1 | Formal step exact |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for category in sorted(by_category):
        item = by_category[category]
        label = f"{category} — {CATEGORY_LABELS.get(category, category)}"
        lines.append(
            f"| {label} | {item.get('n', '')} | "
            f"{item.get('claim_f1', 0):.4f} | {item.get('claim_exact_match', 0):.4f} | "
            f"{item.get('formal_step_f1', 0):.4f} | {item.get('formal_step_exact_match', 0):.4f} |"
        )
    lines.append("")

    lines.append("## 5. Contagem de divergências")
    lines.append("")
    lines.append("### Claims")
    lines.append("")
    for k, v in sorted(claim_status_counts.items()):
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("### Formal steps")
    lines.append("")
    for k, v in sorted(step_status_counts.items()):
        lines.append(f"- **{k}:** {v}")
    lines.append("")

    lines.append("## 6. Legenda dos claims")
    lines.append("")
    for key, label in CLAIM_LABELS.items():
        lines.append(f"- **{key}:** {label}")
    lines.append("")

    lines.append("## 7. Legenda dos formal_steps")
    lines.append("")
    for key, label in STEP_LABELS.items():
        lines.append(f"- **{key}:** {label}")
    lines.append("")

    lines.append("## 8. Tabela completa — solução, gold e saída do agente")
    lines.append("")
    lines.append(
        "Cada item abaixo mostra a solução sintética gerada, o que ela realmente diz "
        "segundo a anotação gold, o que o agente identificou na etapa 3 e o que ele "
        "gerou na etapa 4."
    )
    lines.append("")

    for row in rows:
        lines.append(f"### {row['id']} — Categoria {row['category']} ({row['category_label']})")
        lines.append("")
        lines.append("**Solução gerada:**")
        lines.append("")
        lines.append("> " + row["solution"].replace("\n", "\n> "))
        lines.append("")
        lines.append("**O que a solução realmente diz segundo o gold:**")
        lines.append("")
        lines.append(row["what_solution_really_says"])
        lines.append("")
        lines.append("**Etapa 1 — Entrada:**")
        lines.append("")
        lines.append(f"- input_valid: `{row['stage_1_input_valid']}`")
        lines.append("")
        lines.append("**Etapa 2 — Carregamento:**")
        lines.append("")
        lines.append(f"- load_success: `{row['stage_2_load_success']}`")
        lines.append("")
        lines.append("**Etapa 3 — Claims:**")
        lines.append("")
        lines.append(f"- expected_claims: `{render_set(row['expected_claims'], CLAIM_LABELS)}`")
        lines.append(f"- got_claims: `{render_set(row['got_claims'], CLAIM_LABELS)}`")
        lines.append(f"- missing_claims: `{render_set(row['missing_claims'], CLAIM_LABELS)}`")
        lines.append(f"- extra_claims: `{render_set(row['extra_claims'], CLAIM_LABELS)}`")
        lines.append(f"- claim_status: `{row['claim_status']}`")
        lines.append("")
        lines.append("**Etapa 4 — Formal steps:**")
        lines.append("")
        lines.append(f"- expected_formal_steps: `{render_set(row['expected_formal_steps'], STEP_LABELS)}`")
        lines.append(f"- got_formal_steps: `{render_set(row['got_formal_steps'], STEP_LABELS)}`")
        lines.append(f"- missing_formal_steps: `{render_set(row['missing_formal_steps'], STEP_LABELS)}`")
        lines.append(f"- extra_formal_steps: `{render_set(row['extra_formal_steps'], STEP_LABELS)}`")
        lines.append(f"- formal_step_status: `{row['formal_step_status']}`")
        if row.get("extraction_error"):
            lines.append("")
            lines.append(f"**Erro de extração:** `{row['extraction_error']}`")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Gera relatório completo do benchmark F2Q8 etapas 1 a 4."
    )
    parser.add_argument("--gold", default=str(DEFAULT_GOLD))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD))
    parser.add_argument("--out-csv", default=str(DEFAULT_OUT_CSV))
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON))
    args = parser.parse_args()

    gold_path = Path(args.gold)
    report_path = Path(args.report)
    out_md = Path(args.out_md)
    out_csv = Path(args.out_csv)
    out_json = Path(args.out_json)

    if not gold_path.exists():
        raise FileNotFoundError(f"Gold CSV não encontrado: {gold_path}")
    if not report_path.exists():
        raise FileNotFoundError(f"Relatório JSON não encontrado: {report_path}")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    gold = load_gold(gold_path)
    report = load_report(report_path)
    rows = build_complete_rows(gold, report)
    summary = report["summary"]

    write_markdown(summary, rows, out_md)
    write_csv(rows, out_csv)
    write_json(summary, rows, out_json)

    print("Arquivos gerados:")
    print(f"- {out_md}")
    print(f"- {out_csv}")
    print(f"- {out_json}")


if __name__ == "__main__":
    main()
