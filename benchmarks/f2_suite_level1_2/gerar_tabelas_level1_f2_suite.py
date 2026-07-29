from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
BENCH_DIR = ROOT / "benchmarks" / "f2_suite_level1_2"
REPORTS_DIR = BENCH_DIR / "reports"

DEFAULT_REPORT = REPORTS_DIR / "level1_f2_suite_report_500.json"

OUT_DETAILED = REPORTS_DIR / "tabela_detalhada_level1_f2_suite_500.csv"
OUT_GLOBAL = REPORTS_DIR / "resumo_global_level1_f2_suite_500.csv"
OUT_BY_PROBLEM = REPORTS_DIR / "resumo_por_questao_level1_f2_suite_500.csv"
OUT_BY_CATEGORY = REPORTS_DIR / "resumo_por_categoria_level1_f2_suite_500.csv"
OUT_BY_PROBLEM_CATEGORY = REPORTS_DIR / "resumo_por_questao_categoria_level1_f2_suite_500.csv"
OUT_DIVERGENCES = REPORTS_DIR / "divergencias_level1_f2_suite_500.csv"
OUT_MD = REPORTS_DIR / "relatorio_level1_f2_suite_500.md"


CATEGORY_LABELS = {
    "A": "Correta",
    "B": "Erro de conta",
    "C": "Erro de conceito",
    "D": "Parcial",
    "E": "Formato difícil",
    "F": "Adversarial",
}


def join_items(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(str(x) for x in value)
    if isinstance(value, set):
        return "|".join(sorted(str(x) for x in value))
    return str(value)


def pct(value: Any) -> str:
    if isinstance(value, (float, int)):
        return f"{100 * value:.2f}%"
    return str(value)


def status(missing: Iterable[str], extra: Iterable[str]) -> str:
    missing = list(missing or [])
    extra = list(extra or [])
    if not missing and not extra:
        return "OK"
    if missing and extra:
        return "FALTOU_E_EXTRAIU_A_MAIS"
    if missing:
        return "FALTOU"
    return "EXTRAIU_A_MAIS"


def write_csv(rows: List[Dict[str, Any]], path: Path, fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            flat = {}
            for key in fieldnames:
                value = row.get(key, "")
                if isinstance(value, (list, set)):
                    value = join_items(value)
                elif isinstance(value, dict):
                    value = json.dumps(value, ensure_ascii=False)
                flat[key] = value
            writer.writerow(flat)


def flatten_summary_row(label_type: str, label: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tipo": label_type,
        "grupo": label,
        "n": data.get("n"),
        "stage_1_input_valid_rate": data.get("stage_1_input_valid_rate"),
        "stage_2_load_success_rate": data.get("stage_2_load_success_rate"),
        "stage_3_extraction_success_rate": data.get("stage_3_extraction_success_rate"),
        "claim_tp": data.get("claim_tp"),
        "claim_fp": data.get("claim_fp"),
        "claim_fn": data.get("claim_fn"),
        "claim_precision": data.get("claim_precision"),
        "claim_recall": data.get("claim_recall"),
        "claim_f1": data.get("claim_f1"),
        "claim_exact_match": data.get("claim_exact_match"),
        "formal_step_tp": data.get("formal_step_tp"),
        "formal_step_fp": data.get("formal_step_fp"),
        "formal_step_fn": data.get("formal_step_fn"),
        "formal_step_precision": data.get("formal_step_precision"),
        "formal_step_recall": data.get("formal_step_recall"),
        "formal_step_f1": data.get("formal_step_f1"),
        "formal_step_exact_match": data.get("formal_step_exact_match"),
    }


def build_detailed_rows(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []

    for item in report["rows"]:
        claim_status = status(
            item.get("missing_claims", []),
            item.get("extra_claims", []),
        )
        formal_step_status = status(
            item.get("missing_formal_steps", []),
            item.get("extra_formal_steps", []),
        )

        claim_metrics = item.get("claim_metrics", {})
        step_metrics = item.get("formal_step_metrics", {})

        rows.append(
            {
                "id": item.get("id"),
                "problem_id": item.get("problem_id"),
                "category": item.get("category"),
                "category_label": CATEGORY_LABELS.get(item.get("category"), item.get("category")),
                "solution": item.get("solution"),
                "stage_1_input_valid": item.get("input_valid"),
                "stage_2_load_success": item.get("load_success"),
                "assets": item.get("assets"),
                "extraction_error": item.get("extraction_error"),
                "expected_claims": item.get("expected_claims", []),
                "got_claims": item.get("got_claims", []),
                "missing_claims": item.get("missing_claims", []),
                "extra_claims": item.get("extra_claims", []),
                "claim_status": claim_status,
                "expected_formal_steps": item.get("expected_formal_steps", []),
                "got_formal_steps": item.get("got_formal_steps", []),
                "missing_formal_steps": item.get("missing_formal_steps", []),
                "extra_formal_steps": item.get("extra_formal_steps", []),
                "formal_step_status": formal_step_status,
                "claim_tp_row": claim_metrics.get("tp"),
                "claim_fp_row": claim_metrics.get("fp"),
                "claim_fn_row": claim_metrics.get("fn"),
                "claim_precision_row": claim_metrics.get("precision"),
                "claim_recall_row": claim_metrics.get("recall"),
                "claim_f1_row": claim_metrics.get("f1"),
                "claim_exact_row": claim_metrics.get("exact"),
                "formal_step_tp_row": step_metrics.get("tp"),
                "formal_step_fp_row": step_metrics.get("fp"),
                "formal_step_fn_row": step_metrics.get("fn"),
                "formal_step_precision_row": step_metrics.get("precision"),
                "formal_step_recall_row": step_metrics.get("recall"),
                "formal_step_f1_row": step_metrics.get("f1"),
                "formal_step_exact_row": step_metrics.get("exact"),
            }
        )

    return rows


def write_markdown(summary: Dict[str, Any], detailed_rows: List[Dict[str, Any]], path: Path) -> None:
    global_summary = summary["global"]
    by_problem = summary["by_problem"]
    by_category = summary["by_category"]

    divergences = [
        r for r in detailed_rows
        if r["claim_status"] != "OK"
        or r["formal_step_status"] != "OK"
        or r["extraction_error"]
    ]

    lines: List[str] = []

    lines.append("# Benchmark F2 suite — Nível 1")
    lines.append("")
    lines.append("## 1. Escopo")
    lines.append("")
    lines.append("Este relatório avalia a 2ª fase nas etapas pré-Lean:")
    lines.append("")
    lines.append("- entrada `problem_id + solution`;")
    lines.append("- carregamento dos assets do problema;")
    lines.append("- extração de claims matemáticos;")
    lines.append("- geração/mapeamento de `formal_steps`.")
    lines.append("")
    lines.append("Ele ainda não mede execução Lean, `student_claim_checks`, ajuste de rubrica nem score final.")
    lines.append("")

    lines.append("## 2. Resumo global")
    lines.append("")
    lines.append("| Métrica | Valor |")
    lines.append("|---|---:|")
    lines.append(f"| n | {global_summary['n']} |")
    lines.append(f"| Entrada válida | {pct(global_summary['stage_1_input_valid_rate'])} |")
    lines.append(f"| Assets carregados | {pct(global_summary['stage_2_load_success_rate'])} |")
    lines.append(f"| Extração executada | {pct(global_summary['stage_3_extraction_success_rate'])} |")
    lines.append(f"| Claim precision | {global_summary['claim_precision']:.4f} |")
    lines.append(f"| Claim recall | {global_summary['claim_recall']:.4f} |")
    lines.append(f"| Claim F1 | {global_summary['claim_f1']:.4f} |")
    lines.append(f"| Formal step precision | {global_summary['formal_step_precision']:.4f} |")
    lines.append(f"| Formal step recall | {global_summary['formal_step_recall']:.4f} |")
    lines.append(f"| Formal step F1 | {global_summary['formal_step_f1']:.4f} |")
    lines.append("")

    lines.append("## 3. Desempenho por questão")
    lines.append("")
    lines.append("| Questão | n | Claim F1 | Formal step F1 | Claim FP | Claim FN | Step FP | Step FN |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for problem_id, data in by_problem.items():
        lines.append(
            f"| {problem_id} | {data['n']} | {data['claim_f1']:.4f} | "
            f"{data['formal_step_f1']:.4f} | {data['claim_fp']} | {data['claim_fn']} | "
            f"{data['formal_step_fp']} | {data['formal_step_fn']} |"
        )
    lines.append("")

    lines.append("## 4. Desempenho por categoria")
    lines.append("")
    lines.append("| Categoria | n | Claim F1 | Formal step F1 | Claim FP | Claim FN | Step FP | Step FN |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for category, data in by_category.items():
        label = CATEGORY_LABELS.get(category, category)
        lines.append(
            f"| {category} — {label} | {data['n']} | {data['claim_f1']:.4f} | "
            f"{data['formal_step_f1']:.4f} | {data['claim_fp']} | {data['claim_fn']} | "
            f"{data['formal_step_fp']} | {data['formal_step_fn']} |"
        )
    lines.append("")

    lines.append("## 5. Casos com divergência")
    lines.append("")
    lines.append(f"Total de casos com alguma divergência: **{len(divergences)}**.")
    lines.append("")
    lines.append("| id | questão | categoria | claim_status | formal_step_status | missing_claims | extra_claims | missing_steps | extra_steps |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in divergences[:80]:
        lines.append(
            f"| {r['id']} | {r['problem_id']} | {r['category']} | "
            f"{r['claim_status']} | {r['formal_step_status']} | "
            f"{join_items(r['missing_claims']) or '∅'} | "
            f"{join_items(r['extra_claims']) or '∅'} | "
            f"{join_items(r['missing_formal_steps']) or '∅'} | "
            f"{join_items(r['extra_formal_steps']) or '∅'} |"
        )

    if len(divergences) > 80:
        lines.append("")
        lines.append(f"Foram omitidas {len(divergences) - 80} divergências nesta prévia em Markdown; a tabela CSV contém todas.")

    lines.append("")
    lines.append("## 6. Arquivos gerados")
    lines.append("")
    lines.append(f"- `{OUT_DETAILED}`")
    lines.append(f"- `{OUT_GLOBAL}`")
    lines.append(f"- `{OUT_BY_PROBLEM}`")
    lines.append(f"- `{OUT_BY_CATEGORY}`")
    lines.append(f"- `{OUT_BY_PROBLEM_CATEGORY}`")
    lines.append(f"- `{OUT_DIVERGENCES}`")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    report = json.loads(DEFAULT_REPORT.read_text(encoding="utf-8"))
    summary = report["summary"]

    detailed_rows = build_detailed_rows(report)

    detailed_fieldnames = [
        "id",
        "problem_id",
        "category",
        "category_label",
        "solution",
        "stage_1_input_valid",
        "stage_2_load_success",
        "assets",
        "extraction_error",
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
        "claim_tp_row",
        "claim_fp_row",
        "claim_fn_row",
        "claim_precision_row",
        "claim_recall_row",
        "claim_f1_row",
        "claim_exact_row",
        "formal_step_tp_row",
        "formal_step_fp_row",
        "formal_step_fn_row",
        "formal_step_precision_row",
        "formal_step_recall_row",
        "formal_step_f1_row",
        "formal_step_exact_row",
    ]

    summary_fieldnames = [
        "tipo",
        "grupo",
        "n",
        "stage_1_input_valid_rate",
        "stage_2_load_success_rate",
        "stage_3_extraction_success_rate",
        "claim_tp",
        "claim_fp",
        "claim_fn",
        "claim_precision",
        "claim_recall",
        "claim_f1",
        "claim_exact_match",
        "formal_step_tp",
        "formal_step_fp",
        "formal_step_fn",
        "formal_step_precision",
        "formal_step_recall",
        "formal_step_f1",
        "formal_step_exact_match",
    ]

    global_rows = [flatten_summary_row("global", "F2_suite", summary["global"])]

    by_problem_rows = [
        flatten_summary_row("problem", problem_id, data)
        for problem_id, data in summary["by_problem"].items()
    ]

    by_category_rows = [
        flatten_summary_row(
            "category",
            f"{category} — {CATEGORY_LABELS.get(category, category)}",
            data,
        )
        for category, data in summary["by_category"].items()
    ]

    by_problem_category_rows = [
        flatten_summary_row("problem_category", key, data)
        for key, data in summary["by_problem_category"].items()
    ]

    divergence_rows = [
        r for r in detailed_rows
        if r["claim_status"] != "OK"
        or r["formal_step_status"] != "OK"
        or r["extraction_error"]
    ]

    write_csv(detailed_rows, OUT_DETAILED, detailed_fieldnames)
    write_csv(global_rows, OUT_GLOBAL, summary_fieldnames)
    write_csv(by_problem_rows, OUT_BY_PROBLEM, summary_fieldnames)
    write_csv(by_category_rows, OUT_BY_CATEGORY, summary_fieldnames)
    write_csv(by_problem_category_rows, OUT_BY_PROBLEM_CATEGORY, summary_fieldnames)
    write_csv(divergence_rows, OUT_DIVERGENCES, detailed_fieldnames)
    write_markdown(summary, detailed_rows, OUT_MD)

    print("Tabelas geradas:")
    for path in [
        OUT_DETAILED,
        OUT_GLOBAL,
        OUT_BY_PROBLEM,
        OUT_BY_CATEGORY,
        OUT_BY_PROBLEM_CATEGORY,
        OUT_DIVERGENCES,
        OUT_MD,
    ]:
        print("-", path)


if __name__ == "__main__":
    main()
