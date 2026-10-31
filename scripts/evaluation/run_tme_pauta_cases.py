"""Replay only versioned small TME DIGITAL fixtures, optionally using local Lean."""
import argparse
from collections import Counter
import json
from pathlib import Path

from confia_lean_auditor.tme.registry import TME_PROBLEMS, audit_tme

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = {"TME2_P1_PILOT": "tme2_p1_digital", "TME2026P3": "tme2_p3_digital"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--problem", choices=tuple(TME_PROBLEMS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lean-cases", default="", help="Comma-separated fixture IDs; local Lean only")
    args = parser.parse_args()
    cases = json.loads((ROOT / "tests/fixtures" / FIXTURES[args.problem] / "cases.json").read_text())
    lean_ids = set(filter(None, args.lean_cases.split(",")))
    if not lean_ids <= {c["id"] for c in cases}:
        parser.error("Lean selection contains an unknown fixture ID")
    args.output.mkdir(parents=True, exist_ok=False)
    rows, covered, sources, outcomes, fact_outcomes = [], set(), Counter(), Counter(), Counter()
    formal_checks = []
    for case in cases:
        bridge, assessment = audit_tme(args.problem, {case["item"]: case["text"]},
            solution_id=case["id"], use_lean=case["id"] in lean_ids,
            run_id=args.problem + "-" + case["id"])
        item = next(i for i in assessment.items if i.item_id == case["item"])
        passed = item.points_awarded == case["points"]
        if "selected_path" in case:
            passed = passed and item.selected_method_path == case["selected_path"]
        if "band" in case:
            portion = item.children[2] if case["item"] == "c" else item
            passed = passed and portion.selected_band == case["band"]
            if "band_points" in case:
                passed = passed and portion.points_awarded == case["band_points"]
        relevant = [e for e in bridge.evidence.obligations if e.obligation_id.startswith(case["item"] + ".")]
        covered.update(e.obligation_id for e in relevant if e.status == "supported")
        outcomes.update(e.status for e in relevant)
        sources.update(f.verification_source for f in bridge.auditor.facts)
        fact_outcomes.update(f.verification.status for f in bridge.auditor.facts)
        formal_checks.extend(dict(case_id=case["id"], fact_id=f.fact_id,
            status=f.verification.status, certificate=f.verification.artifact_ref,
            number_domain=f.student_check["data"].get("number_domain", "Z"),
            statement=f.student_check["lean_statement"])
            for f in bridge.auditor.facts if f.student_check)
        payload = dict(input=case, passed=passed, bridge=bridge.model_dump(mode="json"),
            assessment=assessment.model_dump(mode="json"))
        (args.output / (case["id"] + ".json")).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        rows.append(dict(id=case["id"], item=case["item"], points=str(item.points_awarded),
            expected_points=case["points"], passed=passed, selected_path=item.selected_method_path,
            obligation_statuses={e.obligation_id: e.status for e in relevant},
            credit_evidence_refs=list(item.credit_evidence_refs)))
    summary = dict(problem_id=args.problem, cases=len(cases), passed=sum(r["passed"] for r in rows),
        lean_selected_cases=sorted(lean_ids), supported_obligations=sorted(covered),
        relevant_obligation_outcomes=dict(outcomes), verification_sources=dict(sources),
        verification_outcomes=dict(fact_outcomes), formal_checks=formal_checks, cases_results=rows,
        external_api_calls=0)
    (args.output / "replay_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(f"{summary['passed']}/{len(cases)} cases; {len(covered)} obligations; {len(formal_checks)} local Lean checks")
    return 0 if summary["passed"] == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
