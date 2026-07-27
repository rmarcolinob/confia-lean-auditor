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

DEFAULT_OUT_MD = BENCH_DIR / "reports" / "relatorio_detalhado_sem_resumo_benchmark_f2q8_stage1_4.md"
DEFAULT_OUT_CSV = BENCH_DIR / "reports" / "tabela_detalhada_sem_resumo_benchmark_f2q8_stage1_4.csv"
DEFAULT_OUT_JSON = BENCH_DIR / "reports" / "relatorio_detalhado_sem_resumo_benchmark_f2q8_stage1_4.json"


CLAIM_ORDER = [
    "matrix_transformation",
    "determinant_formula",
    "alternating_sum",
    "final_answer",
]

STEP_ORDER = [
    "f2q8_bridge",
    "f2q8_coldiff_det_one",
    "f2q8_determinant_formula",
    "f2q8_final_sum",
]

CLAIM_LABELS = {
    "matrix_transformation": "Transformação por diferenças sucessivas de colunas",
    "determinant_formula": "Fórmula geral det(A_k)=(-1)^(k-1)k",
    "alternating_sum": "Redução à soma alternada 1-2+3-4+...+2025",
    "final_answer": "Resposta final 1013",
}

CLAIM_QUESTIONS = {
    "matrix_transformation": (
        "A solução realmente afirma uma operação de diferenças sucessivas de colunas, "
        "por exemplo C_j <- C_j - C_{j-1}, subtração de colunas consecutivas, ou matriz auxiliar de diferenças?"
    ),
    "determinant_formula": (
        "A solução realmente afirma ou deriva a fórmula correta det(A_k)=(-1)^(k-1)k?"
    ),
    "alternating_sum": (
        "A solução realmente transforma a soma dos determinantes em 1-2+3-4+...+2025 "
        "ou em uma soma alternada equivalente?"
    ),
    "final_answer": (
        "A solução realmente apresenta 1013 como resposta final do problema, em contexto matemático da soma pedida?"
    ),
}

STEP_LABELS = {
    "f2q8_bridge": "Ponte formal: maxMatrix * colDiffMatrix = transformedShape",
    "f2q8_coldiff_det_one": "Matriz de diferenças tem determinante 1",
    "f2q8_determinant_formula": "Teorema formal da fórmula geral do determinante",
    "f2q8_final_sum": "Verificação formal da soma final até 2025",
}

STEP_QUESTIONS = {
    "f2q8_bridge": (
        "A solução fornece evidência textual suficiente para acionar a ponte formal entre a matriz original "
        "maxMatrix e a matriz transformada por diferenças de colunas?"
    ),
    "f2q8_coldiff_det_one": (
        "A solução fornece evidência textual suficiente de que a matriz de diferenças tem determinante 1 "
        "ou de que a transformação preserva o determinante?"
    ),
    "f2q8_determinant_formula": (
        "A solução fornece evidência textual suficiente para acionar a verificação formal da fórmula "
        "det(A_k)=(-1)^(k-1)k?"
    ),
    "f2q8_final_sum": (
        "A solução fornece evidência textual suficiente para acionar a verificação formal da soma "
        "Σ_{k=1}^{2025} (-1)^(k-1)k = 1013?"
    ),
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


def pipe(items: Iterable[str]) -> str:
    items = sorted(set(items))
    return "|".join(items)


def yes_no(value: bool) -> str:
    return "SIM" if value else "NÃO"


def decision(expected: bool, got: bool) -> str:
    if expected and got:
        return "TP"
    if expected and not got:
        return "FN"
    if not expected and got:
        return "FP"
    return "TN"


def decision_explanation(expected: bool, got: bool) -> str:
    d = decision(expected, got)
    return {
        "TP": "correto: a solução continha esse item e o agente identificou",
        "FN": "falso negativo: a solução continha esse item, mas o agente não identificou",
        "FP": "falso positivo: a solução não continha esse item segundo o gold, mas o agente identificou",
        "TN": "correto: a solução não continha esse item e o agente não identificou",
    }[d]


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


def load_gold(path: Path) -> Dict[str, Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {row["id"]: row for row in rows}


def load_report(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def try_run_extractor(solution: str) -> Dict[str, Any]:
    """
    Tenta executar o extrator atual do repositório para recuperar evidências textuais,
    descrições e confidence dos claims/formal_steps. Se falhar, o relatório ainda é
    gerado usando apenas o JSON do benchmark.
    """
    try:
        from confia_lean_auditor.claims.extractors.ita2025f2q8 import (  # type: ignore
            detect_features,
            extract_claims_ita2025f2q8,
        )

        features = detect_features(solution)
        extraction = extract_claims_ita2025f2q8(solution)

        claim_details = {}
        for claim in extraction.claims:
            claim_details[claim.type] = {
                "id": getattr(claim, "id", ""),
                "type": getattr(claim, "type", ""),
                "text": getattr(claim, "text", ""),
                "evidence": getattr(claim, "evidence", ""),
                "confidence": getattr(claim, "confidence", None),
                "normalized": getattr(claim, "normalized", {}),
            }

        step_details = {}
        for step in extraction.formal_steps:
            step_details[step.type] = {
                "id": getattr(step, "id", ""),
                "type": getattr(step, "type", ""),
                "description": getattr(step, "description", ""),
                "evidence": getattr(step, "evidence", ""),
                "lhs": getattr(step, "lhs", ""),
                "rhs": getattr(step, "rhs", ""),
                "lean_method": getattr(step, "lean_method", ""),
                "supports_claim_types": getattr(step, "supports_claim_types", []),
                "supports_rubric_items": getattr(step, "supports_rubric_items", []),
            }

        return {
            "extractor_available": True,
            "features": features,
            "claim_details": claim_details,
            "step_details": step_details,
        }

    except Exception as exc:
        return {
            "extractor_available": False,
            "extractor_error": repr(exc),
            "features": {},
            "claim_details": {},
            "step_details": {},
        }


def asset_status() -> Dict[str, Any]:
    paths = {
        "problem_json": ROOT / "problems" / "ITA2025F2Q8" / "problem.json",
        "rubric_json": ROOT / "problems" / "ITA2025F2Q8" / "rubric.json",
        "microclaims_json": ROOT / "problems" / "ITA2025F2Q8" / "microclaims.json",
        "lean_statement": ROOT / "ConfiaLeanAuditor" / "Problems" / "ITA2025F2Q8" / "Statement.lean",
        "extractor_py": ROOT / "app" / "confia_lean_auditor" / "claims" / "extractors" / "ita2025f2q8.py",
        "attempt_builder_py": ROOT / "app" / "confia_lean_auditor" / "lean" / "attempt_builders" / "ita2025f2q8.py",
    }

    result = {}
    for name, path in paths.items():
        result[name] = {
            "path": str(path.relative_to(ROOT)) if path.exists() else str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
        }
    return result


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
        solution = g.get("solution", "")

        extractor = try_run_extractor(solution)

        claim_rows: List[Dict[str, Any]] = []
        for claim_type in CLAIM_ORDER:
            expected = claim_type in expected_claims
            got = claim_type in got_claims
            detail = extractor.get("claim_details", {}).get(claim_type, {})
            claim_rows.append(
                {
                    "claim_type": claim_type,
                    "claim_label": CLAIM_LABELS[claim_type],
                    "gold_question": CLAIM_QUESTIONS[claim_type],
                    "gold_expected_present": expected,
                    "agent_detected": got,
                    "decision": decision(expected, got),
                    "decision_explanation": decision_explanation(expected, got),
                    "agent_claim_id": detail.get("id", ""),
                    "agent_claim_text": detail.get("text", ""),
                    "agent_evidence": detail.get("evidence", ""),
                    "agent_confidence": detail.get("confidence", None),
                }
            )

        step_rows: List[Dict[str, Any]] = []
        for step_type in STEP_ORDER:
            expected = step_type in expected_steps
            got = step_type in got_steps
            detail = extractor.get("step_details", {}).get(step_type, {})
            step_rows.append(
                {
                    "formal_step_type": step_type,
                    "formal_step_label": STEP_LABELS[step_type],
                    "gold_question": STEP_QUESTIONS[step_type],
                    "gold_expected_present": expected,
                    "agent_generated": got,
                    "decision": decision(expected, got),
                    "decision_explanation": decision_explanation(expected, got),
                    "agent_step_id": detail.get("id", ""),
                    "agent_description": detail.get("description", ""),
                    "agent_evidence": detail.get("evidence", ""),
                    "lean_method": detail.get("lean_method", ""),
                    "supports_claim_types": detail.get("supports_claim_types", []),
                    "supports_rubric_items": detail.get("supports_rubric_items", []),
                }
            )

        item = {
            "id": row_id,
            "problem_id": g.get("problem_id", "ITA2025F2Q8"),
            "category": g.get("category", r.get("category", "")),
            "category_label": CATEGORY_LABELS.get(
                g.get("category", r.get("category", "")),
                g.get("category", r.get("category", "")),
            ),
            "solution": solution,
            "stage_1": {
                "input_valid": r.get("input_valid"),
                "problem_id_received": g.get("problem_id", "ITA2025F2Q8"),
                "solution_received": solution,
                "solution_char_count": len(solution),
                "solution_word_count": len(solution.split()),
                "input_error": r.get("input_error"),
            },
            "stage_2": {
                "load_success": r.get("load_success"),
                "asset_status": asset_status(),
                "load_error": r.get("load_error"),
            },
            "stage_3": {
                "expected_claims_raw": sorted(expected_claims),
                "got_claims_raw": sorted(got_claims),
                "missing_claims_raw": sorted(expected_claims - got_claims),
                "extra_claims_raw": sorted(got_claims - expected_claims),
                "claim_status": status(expected_claims, got_claims),
                "claim_precision_row": r.get("claim_metrics", {}).get("precision"),
                "claim_recall_row": r.get("claim_metrics", {}).get("recall"),
                "claim_f1_row": r.get("claim_metrics", {}).get("f1"),
                "extractor_available_for_evidence": extractor.get("extractor_available"),
                "extractor_error": extractor.get("extractor_error"),
                "detected_features": extractor.get("features", {}),
                "claim_decisions": claim_rows,
                "extraction_error": r.get("extraction_error"),
            },
            "stage_4": {
                "expected_formal_steps_raw": sorted(expected_steps),
                "got_formal_steps_raw": sorted(got_steps),
                "missing_formal_steps_raw": sorted(expected_steps - got_steps),
                "extra_formal_steps_raw": sorted(got_steps - expected_steps),
                "formal_step_status": status(expected_steps, got_steps),
                "formal_step_precision_row": r.get("formal_step_metrics", {}).get("precision"),
                "formal_step_recall_row": r.get("formal_step_metrics", {}).get("recall"),
                "formal_step_f1_row": r.get("formal_step_metrics", {}).get("f1"),
                "formal_step_decisions": step_rows,
            },
        }
        complete.append(item)

    return complete


def write_flat_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "id",
        "problem_id",
        "category",
        "category_label",
        "solution",
        "stage_1_input_valid",
        "stage_1_solution_char_count",
        "stage_1_solution_word_count",
        "stage_2_load_success",
        "expected_claims_raw",
        "got_claims_raw",
        "missing_claims_raw",
        "extra_claims_raw",
        "claim_status",
        "claim_precision_row",
        "claim_recall_row",
        "claim_f1_row",
        "expected_formal_steps_raw",
        "got_formal_steps_raw",
        "missing_formal_steps_raw",
        "extra_formal_steps_raw",
        "formal_step_status",
        "formal_step_precision_row",
        "formal_step_recall_row",
        "formal_step_f1_row",
    ]

    for claim_type in CLAIM_ORDER:
        prefix = f"claim_{claim_type}"
        fieldnames += [
            f"{prefix}_gold_expected_present",
            f"{prefix}_agent_detected",
            f"{prefix}_decision",
            f"{prefix}_agent_evidence",
            f"{prefix}_agent_confidence",
        ]

    for step_type in STEP_ORDER:
        prefix = f"step_{step_type}"
        fieldnames += [
            f"{prefix}_gold_expected_present",
            f"{prefix}_agent_generated",
            f"{prefix}_decision",
            f"{prefix}_agent_evidence",
            f"{prefix}_lean_method",
        ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            flat = {
                "id": row["id"],
                "problem_id": row["problem_id"],
                "category": row["category"],
                "category_label": row["category_label"],
                "solution": row["solution"],
                "stage_1_input_valid": row["stage_1"]["input_valid"],
                "stage_1_solution_char_count": row["stage_1"]["solution_char_count"],
                "stage_1_solution_word_count": row["stage_1"]["solution_word_count"],
                "stage_2_load_success": row["stage_2"]["load_success"],
                "expected_claims_raw": pipe(row["stage_3"]["expected_claims_raw"]),
                "got_claims_raw": pipe(row["stage_3"]["got_claims_raw"]),
                "missing_claims_raw": pipe(row["stage_3"]["missing_claims_raw"]),
                "extra_claims_raw": pipe(row["stage_3"]["extra_claims_raw"]),
                "claim_status": row["stage_3"]["claim_status"],
                "claim_precision_row": row["stage_3"]["claim_precision_row"],
                "claim_recall_row": row["stage_3"]["claim_recall_row"],
                "claim_f1_row": row["stage_3"]["claim_f1_row"],
                "expected_formal_steps_raw": pipe(row["stage_4"]["expected_formal_steps_raw"]),
                "got_formal_steps_raw": pipe(row["stage_4"]["got_formal_steps_raw"]),
                "missing_formal_steps_raw": pipe(row["stage_4"]["missing_formal_steps_raw"]),
                "extra_formal_steps_raw": pipe(row["stage_4"]["extra_formal_steps_raw"]),
                "formal_step_status": row["stage_4"]["formal_step_status"],
                "formal_step_precision_row": row["stage_4"]["formal_step_precision_row"],
                "formal_step_recall_row": row["stage_4"]["formal_step_recall_row"],
                "formal_step_f1_row": row["stage_4"]["formal_step_f1_row"],
            }

            claim_by_type = {x["claim_type"]: x for x in row["stage_3"]["claim_decisions"]}
            for claim_type in CLAIM_ORDER:
                item = claim_by_type[claim_type]
                prefix = f"claim_{claim_type}"
                flat[f"{prefix}_gold_expected_present"] = item["gold_expected_present"]
                flat[f"{prefix}_agent_detected"] = item["agent_detected"]
                flat[f"{prefix}_decision"] = item["decision"]
                flat[f"{prefix}_agent_evidence"] = item["agent_evidence"]
                flat[f"{prefix}_agent_confidence"] = item["agent_confidence"]

            step_by_type = {x["formal_step_type"]: x for x in row["stage_4"]["formal_step_decisions"]}
            for step_type in STEP_ORDER:
                item = step_by_type[step_type]
                prefix = f"step_{step_type}"
                flat[f"{prefix}_gold_expected_present"] = item["gold_expected_present"]
                flat[f"{prefix}_agent_generated"] = item["agent_generated"]
                flat[f"{prefix}_decision"] = item["decision"]
                flat[f"{prefix}_agent_evidence"] = item["agent_evidence"]
                flat[f"{prefix}_lean_method"] = item["lean_method"]

            writer.writerow(flat)


def write_json(summary: Dict[str, Any], rows: List[Dict[str, Any]], path: Path) -> None:
    payload = {
        "benchmark": "ITA2025F2Q8 — relatório detalhado sem descrição resumida",
        "description": (
            "Cada linha contém a solução inteira, os dados da etapa 1, os assets da etapa 2, "
            "uma decisão binária para cada claim da etapa 3 e uma decisão binária para cada "
            "formal_step da etapa 4. Não há compressão do tipo 'what_solution_really_says'."
        ),
        "summary": summary,
        "claim_order": CLAIM_ORDER,
        "formal_step_order": STEP_ORDER,
        "claim_labels": CLAIM_LABELS,
        "formal_step_labels": STEP_LABELS,
        "rows": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def render_bool(value: Any) -> str:
    if value is True:
        return "SIM"
    if value is False:
        return "NÃO"
    return str(value)


def render_list(value: Iterable[str]) -> str:
    value = list(value)
    if not value:
        return "∅"
    return ", ".join(value)


def write_markdown(summary: Dict[str, Any], rows: List[Dict[str, Any]], path: Path) -> None:
    counts = Counter(row["category"] for row in rows)

    lines: List[str] = []
    lines.append("# Relatório detalhado sem resumo — benchmark ITA2025F2Q8, etapas 1 a 4")
    lines.append("")
    lines.append("Este relatório registra cada solução sintética sem substituir as etapas por uma descrição resumida.")
    lines.append("Para cada solução, cada claim e cada formal_step aparece separadamente com decisão TP/FN/FP/TN.")
    lines.append("")
    lines.append("## Legenda de decisão")
    lines.append("")
    lines.append("- **TP:** o item estava no gold e o agente identificou/gerou.")
    lines.append("- **FN:** o item estava no gold e o agente não identificou/gerou.")
    lines.append("- **FP:** o item não estava no gold e o agente identificou/gerou indevidamente.")
    lines.append("- **TN:** o item não estava no gold e o agente também não identificou/gerou.")
    lines.append("")

    lines.append("## Resumo estatístico global")
    lines.append("")
    for key, value in summary.items():
        if key == "by_category":
            continue
        lines.append(f"- **{key}:** `{value}`")
    lines.append("")

    lines.append("## Distribuição por categoria")
    lines.append("")
    for category in sorted(counts):
        lines.append(f"- **{category} — {CATEGORY_LABELS.get(category, category)}:** {counts[category]}")
    lines.append("")

    lines.append("## Resultado por categoria")
    lines.append("")
    lines.append("| Categoria | n | Claim precision | Claim recall | Claim F1 | Claim exact | Formal precision | Formal recall | Formal F1 | Formal exact |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    by_category = summary.get("by_category", {})
    for category in sorted(by_category):
        item = by_category[category]
        label = f"{category} — {CATEGORY_LABELS.get(category, category)}"
        lines.append(
            f"| {label} | {item.get('n', '')} | "
            f"{item.get('claim_precision', 0):.4f} | {item.get('claim_recall', 0):.4f} | "
            f"{item.get('claim_f1', 0):.4f} | {item.get('claim_exact_match', 0):.4f} | "
            f"{item.get('formal_step_precision', 0):.4f} | {item.get('formal_step_recall', 0):.4f} | "
            f"{item.get('formal_step_f1', 0):.4f} | {item.get('formal_step_exact_match', 0):.4f} |"
        )
    lines.append("")

    lines.append("## Soluções e decisões detalhadas")
    lines.append("")

    for row in rows:
        lines.append(f"---")
        lines.append("")
        lines.append(f"## {row['id']} — Categoria {row['category']} ({row['category_label']})")
        lines.append("")
        lines.append("### Solução gerada integral")
        lines.append("")
        lines.append("> " + row["solution"].replace("\n", "\n> "))
        lines.append("")

        lines.append("### Etapa 1 — Entrada recebida")
        lines.append("")
        lines.append(f"- **problem_id_received:** `{row['stage_1']['problem_id_received']}`")
        lines.append(f"- **input_valid:** `{row['stage_1']['input_valid']}`")
        lines.append(f"- **solution_char_count:** `{row['stage_1']['solution_char_count']}`")
        lines.append(f"- **solution_word_count:** `{row['stage_1']['solution_word_count']}`")
        lines.append(f"- **input_error:** `{row['stage_1']['input_error']}`")
        lines.append("")

        lines.append("### Etapa 2 — Carregamento de assets")
        lines.append("")
        lines.append(f"- **load_success:** `{row['stage_2']['load_success']}`")
        lines.append(f"- **load_error:** `{row['stage_2']['load_error']}`")
        lines.append("")
        lines.append("| Asset | Caminho | Existe? | Tamanho bytes |")
        lines.append("|---|---|---:|---:|")
        for asset_name, asset in row["stage_2"]["asset_status"].items():
            lines.append(
                f"| `{asset_name}` | `{asset['path']}` | {render_bool(asset['exists'])} | {asset['size_bytes']} |"
            )
        lines.append("")

        lines.append("### Etapa 3 — Claims, sem resumo")
        lines.append("")
        lines.append(f"- **expected_claims_raw:** `{render_list(row['stage_3']['expected_claims_raw'])}`")
        lines.append(f"- **got_claims_raw:** `{render_list(row['stage_3']['got_claims_raw'])}`")
        lines.append(f"- **missing_claims_raw:** `{render_list(row['stage_3']['missing_claims_raw'])}`")
        lines.append(f"- **extra_claims_raw:** `{render_list(row['stage_3']['extra_claims_raw'])}`")
        lines.append(f"- **claim_status:** `{row['stage_3']['claim_status']}`")
        lines.append(f"- **claim_precision_row:** `{row['stage_3']['claim_precision_row']}`")
        lines.append(f"- **claim_recall_row:** `{row['stage_3']['claim_recall_row']}`")
        lines.append(f"- **claim_f1_row:** `{row['stage_3']['claim_f1_row']}`")
        lines.append(f"- **extractor_available_for_evidence:** `{row['stage_3']['extractor_available_for_evidence']}`")
        lines.append(f"- **extractor_error:** `{row['stage_3']['extractor_error']}`")
        lines.append(f"- **detected_features:** `{row['stage_3']['detected_features']}`")
        lines.append("")
        lines.append("| Claim | Pergunta gold detalhada | Gold esperava? | Agente detectou? | Decisão | Evidência do agente | Confiança |")
        lines.append("|---|---|---:|---:|---|---|---:|")
        for item in row["stage_3"]["claim_decisions"]:
            evidence = str(item["agent_evidence"]).replace("|", "\\|").replace("\n", " ")
            question = item["gold_question"].replace("|", "\\|")
            lines.append(
                f"| `{item['claim_type']}` — {item['claim_label']} | {question} | "
                f"{yes_no(item['gold_expected_present'])} | {yes_no(item['agent_detected'])} | "
                f"{item['decision']} | {evidence or '∅'} | {item['agent_confidence']} |"
            )
        lines.append("")
        lines.append("Detalhamento textual das decisões dos claims:")
        lines.append("")
        for item in row["stage_3"]["claim_decisions"]:
            lines.append(f"- **{item['claim_type']}**: {item['decision_explanation']}.")
            if item["agent_claim_text"]:
                lines.append(f"  - Texto produzido pelo agente: `{item['agent_claim_text']}`")
            if item["agent_evidence"]:
                lines.append(f"  - Evidência produzida pelo agente: `{item['agent_evidence']}`")
        lines.append("")

        lines.append("### Etapa 4 — Formal steps, sem resumo")
        lines.append("")
        lines.append(f"- **expected_formal_steps_raw:** `{render_list(row['stage_4']['expected_formal_steps_raw'])}`")
        lines.append(f"- **got_formal_steps_raw:** `{render_list(row['stage_4']['got_formal_steps_raw'])}`")
        lines.append(f"- **missing_formal_steps_raw:** `{render_list(row['stage_4']['missing_formal_steps_raw'])}`")
        lines.append(f"- **extra_formal_steps_raw:** `{render_list(row['stage_4']['extra_formal_steps_raw'])}`")
        lines.append(f"- **formal_step_status:** `{row['stage_4']['formal_step_status']}`")
        lines.append(f"- **formal_step_precision_row:** `{row['stage_4']['formal_step_precision_row']}`")
        lines.append(f"- **formal_step_recall_row:** `{row['stage_4']['formal_step_recall_row']}`")
        lines.append(f"- **formal_step_f1_row:** `{row['stage_4']['formal_step_f1_row']}`")
        lines.append("")
        lines.append("| Formal step | Pergunta gold detalhada | Gold esperava? | Agente gerou? | Decisão | Evidência do agente | Método Lean |")
        lines.append("|---|---|---:|---:|---|---|---|")
        for item in row["stage_4"]["formal_step_decisions"]:
            evidence = str(item["agent_evidence"]).replace("|", "\\|").replace("\n", " ")
            question = item["gold_question"].replace("|", "\\|")
            lines.append(
                f"| `{item['formal_step_type']}` — {item['formal_step_label']} | {question} | "
                f"{yes_no(item['gold_expected_present'])} | {yes_no(item['agent_generated'])} | "
                f"{item['decision']} | {evidence or '∅'} | `{item['lean_method'] or '∅'}` |"
            )
        lines.append("")
        lines.append("Detalhamento textual das decisões dos formal_steps:")
        lines.append("")
        for item in row["stage_4"]["formal_step_decisions"]:
            lines.append(f"- **{item['formal_step_type']}**: {item['decision_explanation']}.")
            if item["agent_description"]:
                lines.append(f"  - Descrição produzida pelo agente: `{item['agent_description']}`")
            if item["agent_evidence"]:
                lines.append(f"  - Evidência produzida pelo agente: `{item['agent_evidence']}`")
            if item["supports_claim_types"]:
                lines.append(f"  - Claims suportados: `{item['supports_claim_types']}`")
            if item["supports_rubric_items"]:
                lines.append(f"  - Itens de rubrica suportados: `{item['supports_rubric_items']}`")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Gera relatório detalhado sem resumo do benchmark F2Q8 etapas 1 a 4."
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
    write_flat_csv(rows, out_csv)
    write_json(summary, rows, out_json)

    print("Arquivos gerados:")
    print(f"- {out_md}")
    print(f"- {out_csv}")
    print(f"- {out_json}")


if __name__ == "__main__":
    main()
