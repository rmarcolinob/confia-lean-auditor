#!/usr/bin/env python3
"""Paired comparison of Experiment B runs; no gold or accuracy claims."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from run_ita_semantic_formal_b import safe_path, write_json, EXPERIMENT_DESIGN, AWARD_POLICY, install_guards


def read_results(path, expected_mode):
    rows = {}
    with safe_path(path).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            key = (row["problem_id"], row["solution_id"])
            if key in rows or row["mode_requested"] != expected_mode:
                raise ValueError("Duplicate case or wrong mode")
            score = row["score"]
            if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 10:
                raise ValueError("Non-numeric/out-of-range score")
            rows[key] = row
    return rows


def compare(offline, semantic):
    if not offline or set(offline) != set(semantic):
        raise ValueError("Comparison requires identical, nonempty case sets")
    paired = []
    for key in sorted(offline):
        a, b = offline[key], semantic[key]
        for field in ("source_sha256", "historical_base_sha", "experimental_file_sha256"):
            if not a.get(field) or a[field] != b.get(field):
                raise ValueError("Run provenance mismatch: " + field)
        if a.get("award_policy") != AWARD_POLICY or b.get("award_policy") != AWARD_POLICY:
            raise ValueError("Comparison requires the same current common gate policy")
        fallback = b["fallback_used"]
        if fallback and (b["mode_effective"] != "FORMAL_OFFLINE" or b["score"] != a["score"]):
            raise ValueError("Fallback differs from paired offline result")
        if not fallback and b["mode_effective"] != "SEMANTIC_FORMAL":
            raise ValueError("Inconsistent effective semantic mode")
        a_items = {i["id"]: i["points"] for i in a["rubric_items"]}
        b_items = {i["id"]: i["points"] for i in b["rubric_items"]}
        if set(a_items) != set(b_items):
            raise ValueError("Rubric item sets differ")
        paired.append({"problem_id": key[0], "solution_id": key[1], "formal_score": a["score"],
            "semantic_score": b["score"], "delta": b["score"] - a["score"],
            "fallback_used": fallback,
            "technical_error": a["lean_status"] == "technical_error" or b["lean_status"] == "technical_error",
            "changed_items": [item for item in a_items if a_items[item] != b_items[item]]})
    clean = [p for p in paired if not p["fallback_used"] and not p["technical_error"]]
    def stats(rows):
        return {"cases": len(rows), "mean_delta": sum(r["delta"] for r in rows) / len(rows) if rows else None,
                "increased": sum(r["delta"] > 0 for r in rows), "decreased": sum(r["delta"] < 0 for r in rows),
                "unchanged": sum(r["delta"] == 0 for r in rows)}
    return {"pairs": paired, "all_cases": stats(paired), "semantic_success_without_technical_errors": stats(clean),
            "fallbacks": sum(p["fallback_used"] for p in paired),
            "by_problem": {pid: stats([r for r in paired if r["problem_id"] == pid]) for pid in sorted({r["problem_id"] for r in paired})},
            "experiment_design": EXPERIMENT_DESIGN, "award_policy": AWARD_POLICY, "gold_used": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--semantic", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    install_guards(True)
    result = compare(read_results(args.formal, "FORMAL_OFFLINE"), read_results(args.semantic, "SEMANTIC_FORMAL"))
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_json(args.output_dir / "comparison.json", result)


if __name__ == "__main__":
    main()
