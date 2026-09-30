from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Set

from confia_lean_auditor.claims.extract_claims import extract_claims


ROOT = Path(".")
GOLD = ROOT / "benchmarks/q_suite_level1_v2/gold_500.csv"
OUT_DIR = ROOT / "benchmarks/q_suite_level1_v2/reports"

DETAIL_OUT = OUT_DIR / "tabela_detalhada_level1_q_suite_v2_500.csv"
GLOBAL_OUT = OUT_DIR / "resumo_global_level1_q_suite_v2_500.csv"
BY_PROBLEM_OUT = OUT_DIR / "resumo_por_questao_level1_q_suite_v2_500.csv"
BY_CATEGORY_OUT = OUT_DIR / "resumo_por_categoria_level1_q_suite_v2_500.csv"
BY_PROBLEM_CATEGORY_OUT = OUT_DIR / "resumo_por_questao_categoria_level1_q_suite_v2_500.csv"
DIVERGENCES_OUT = OUT_DIR / "divergencias_level1_q_suite_v2_500.csv"


def read_csv(path: Path) -> List[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_pipe(value: str) -> List[str]:
    return [x for x in (value or "").split("|") if x]


def join_pipe(values: List[str] | Set[str]) -> str:
    return "|".join(sorted(values))


def prf(tp: int, fp: int, fn: int):
    precision = 1.0 if tp + fp == 0 else tp / (tp + fp)
    recall = 1.0 if tp + fn == 0 else tp / (tp + fn)
    f1 = 1.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def summarize(rows: List[dict], group_key: str, group_value: str) -> dict:
    n = len(rows)

    claim_tp = claim_fp = claim_fn = 0
    step_tp = step_fp = step_fn = 0
    claim_exact = 0
    step_exact = 0

    for r in rows:
        e_claims = set(split_pipe(r["expected_claims"]))
        d_claims = set(split_pipe(r["detected_claims"]))
        e_steps = set(split_pipe(r["expected_formal_steps"]))
        d_steps = set(split_pipe(r["detected_formal_steps"]))

        claim_tp += len(e_claims & d_claims)
        claim_fp += len(d_claims - e_claims)
        claim_fn += len(e_claims - d_claims)

        step_tp += len(e_steps & d_steps)
        step_fp += len(d_steps - e_steps)
        step_fn += len(e_steps - d_steps)

        if e_claims == d_claims:
            claim_exact += 1
        if e_steps == d_steps:
            step_exact += 1

    claim_precision, claim_recall, claim_f1 = prf(claim_tp, claim_fp, claim_fn)
    step_precision, step_recall, step_f1 = prf(step_tp, step_fp, step_fn)

    return {
        "tipo": group_key,
        "grupo": group_value,
        "n": n,
        "stage_1_input_valid_rate": 1.0,
        "stage_2_load_success_rate": 1.0,
        "stage_3_extraction_success_rate": 1.0,
        "claim_tp": claim_tp,
        "claim_fp": claim_fp,
        "claim_fn": claim_fn,
        "claim_precision": claim_precision,
        "claim_recall": claim_recall,
        "claim_f1": claim_f1,
        "claim_exact_match": claim_exact / n if n else 1.0,
        "formal_step_tp": step_tp,
        "formal_step_fp": step_fp,
        "formal_step_fn": step_fn,
        "formal_step_precision": step_precision,
        "formal_step_recall": step_recall,
        "formal_step_f1": step_f1,
        "formal_step_exact_match": step_exact / n if n else 1.0,
    }


def main() -> None:
    if not GOLD.exists():
        raise FileNotFoundError(f"Gold não encontrado: {GOLD}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = read_csv(GOLD)
    detailed = []
    divergences = []

    for r in rows:
        extraction = extract_claims(r["problem_id"], r["solution"])

        detected_claims = [c.type for c in extraction.claims]
        detected_steps = [s.type for s in extraction.formal_steps]

        expected_claims = set(split_pipe(r["expected_claims"]))
        expected_steps = set(split_pipe(r["expected_formal_steps"]))
        detected_claims_set = set(detected_claims)
        detected_steps_set = set(detected_steps)

        missing_claims = expected_claims - detected_claims_set
        extra_claims = detected_claims_set - expected_claims
        missing_steps = expected_steps - detected_steps_set
        extra_steps = detected_steps_set - expected_steps

        row = {
            "id": r["id"],
            "problem_id": r["problem_id"],
            "category": r["category"],
            "category_label": r["category_label"],
            "solution": r["solution"],
            "expected_claims": r["expected_claims"],
            "detected_claims": join_pipe(detected_claims),
            "missing_claims": join_pipe(missing_claims),
            "extra_claims": join_pipe(extra_claims),
            "expected_formal_steps": r["expected_formal_steps"],
            "detected_formal_steps": join_pipe(detected_steps),
            "missing_formal_steps": join_pipe(missing_steps),
            "extra_formal_steps": join_pipe(extra_steps),
            "claim_exact_match": expected_claims == detected_claims_set,
            "formal_step_exact_match": expected_steps == detected_steps_set,
        }

        detailed.append(row)

        if missing_claims or extra_claims or missing_steps or extra_steps:
            divergences.append(row)

    detail_fields = [
        "id",
        "problem_id",
        "category",
        "category_label",
        "solution",
        "expected_claims",
        "detected_claims",
        "missing_claims",
        "extra_claims",
        "expected_formal_steps",
        "detected_formal_steps",
        "missing_formal_steps",
        "extra_formal_steps",
        "claim_exact_match",
        "formal_step_exact_match",
    ]

    summary_fields = [
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

    write_csv(DETAIL_OUT, detailed, detail_fields)
    write_csv(DIVERGENCES_OUT, divergences, detail_fields)

    write_csv(
        GLOBAL_OUT,
        [summarize(detailed, "global", "q_suite_v2")],
        summary_fields,
    )

    by_problem = []
    for problem_id in sorted({r["problem_id"] for r in detailed}):
        group = [r for r in detailed if r["problem_id"] == problem_id]
        by_problem.append(summarize(group, "problem", problem_id))
    write_csv(BY_PROBLEM_OUT, by_problem, summary_fields)

    by_category = []
    for category in sorted({r["category"] for r in detailed}):
        group = [r for r in detailed if r["category"] == category]
        by_category.append(summarize(group, "category", category))
    write_csv(BY_CATEGORY_OUT, by_category, summary_fields)

    by_problem_category = []
    keys = sorted({(r["problem_id"], r["category"]) for r in detailed})
    for problem_id, category in keys:
        group = [
            r for r in detailed
            if r["problem_id"] == problem_id and r["category"] == category
        ]
        by_problem_category.append(
            summarize(group, "problem_category", f"{problem_id}::{category}")
        )
    write_csv(BY_PROBLEM_CATEGORY_OUT, by_problem_category, summary_fields)

    print("Arquivos gerados:")
    for path in [
        DETAIL_OUT,
        GLOBAL_OUT,
        BY_PROBLEM_OUT,
        BY_CATEGORY_OUT,
        BY_PROBLEM_CATEGORY_OUT,
        DIVERGENCES_OUT,
    ]:
        print("-", path)

    print()
    print("Resumo por questão:")
    for r in by_problem:
        print(
            r["grupo"],
            "claim_precision=", round(float(r["claim_precision"]), 3),
            "claim_recall=", round(float(r["claim_recall"]), 3),
            "claim_f1=", round(float(r["claim_f1"]), 3),
            "formal_step_precision=", round(float(r["formal_step_precision"]), 3),
            "formal_step_recall=", round(float(r["formal_step_recall"]), 3),
            "formal_step_f1=", round(float(r["formal_step_f1"]), 3),
        )

    print()
    print("Divergências:", len(divergences))


if __name__ == "__main__":
    main()
