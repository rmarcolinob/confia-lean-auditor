#!/usr/bin/env python3
"""Report scoring-policy changes for the same 18 IDs; never compare corpus grades."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics


def compare(before, after, test_summary):
    old_selection = json.loads((before / "selected_cases.json").read_text())
    new_selection = json.loads((after / "selected_cases.json").read_text())
    if old_selection != new_selection or len(old_selection["cases"]) != 18:
        raise ValueError("Exactly the original 18 cases are required")
    ids = [c["dataset_id"] for c in old_selection["cases"]]
    old = {key: json.loads((before / "results" / f"{key}.json").read_text()) for key in ids}
    new = {key: json.loads((after / "results" / f"{key}.json").read_text()) for key in ids}
    if any(r.get("scoring_policy") != "SCORE-POLICY-02" for r in new.values()):
        raise ValueError("Missing scoring-policy result")
    summary = {
        "cases": 18,
        "before_numeric": sum(r["score"] is not None for r in old.values()),
        "before_null": sum(r["score"] is None for r in old.values()),
        "after_numeric": sum(r["score"] is not None for r in new.values()),
        "after_null": sum(r["score"] is None for r in new.values()),
        "mean_coverage": statistics.mean(r["coverage"] for r in new.values()),
        "mean_estimated_points": statistics.mean(r["estimated_points"] for r in new.values() if r["estimated_points"] is not None)
            if any(r["estimated_points"] is not None for r in new.values()) else None,
        "needs_review": sum(r["needs_review"] for r in new.values()),
        "verdict_distribution": dict(Counter(r["verdict"] for r in new.values())),
        "residual_null_reasons": {key: r["unscorable_reason"] for key, r in new.items() if r["score"] is None},
    }
    (after / "score_policy_comparison.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    state = json.loads((after / "environment_snapshot.json").read_text())
    lines = ["# SCORE-POLICY-02", "", "## Política antiga e nova", "",
        "Antes: qualquer points=null impedia a nota global. Agora AuditResponse.score soma suggested_points de todos os critérios.",
        "points e verified_points preservam a primeira passagem: crédito apoiado, zero refutado ou null indeterminado. O termo verified refere-se ao subtotal decidido pela primeira passagem, que inclui claims textuais, não apenas provas Lean.",
        "evaluated_score e evaluated_max_score permanecem intactos. coverage = evaluated_max_score/max_score. estimated_points = score - evaluated_score. Um critério estimado em zero continua explicitamente secundário e requer revisão, embora não aumente estimated_points.",
        "A decisão TeacherDecision/TME final_points permanece independente; não houve alteração desses módulos. Sua filtragem preexistente da sugestão normalizada diante de indisponibilidade técnica/indeterminação foi preservada; score bruto e metadados novos estão disponíveis na API.",
        "", "## Adjudicador secundário", "",
        "Uma chamada semântica por solução, somente para critérios pendentes. Recebe texto integral, problema, pauta oficial, critérios, claims, microclaims e checkers. Não recebe notas ou labels sintéticas.",
        "Valores permitidos: zero ou máximo oficial de cada critério. Exige citação literal não vazia da solução e justificativa. Validação local rejeita valores intermediários, booleanos, critérios extras/ausentes e evidência inventada. Refutações decididas ficam fora da chamada. Status matemáticos, claims e estados técnicos não são modificados.",
        "Modelo padrão: gpt-4o-mini, configurável por CONFIA_SECONDARY_MODEL. Request/response hashes, versão do prompt e modelo retornado ficam no resultado. Há timeout de 45 s por chamada e tentativas limitadas. Falha do serviço não é convertida em zero.",
        "Referência de implementação: [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).",
        "", "## Casos sem nota global", "",
        "EMPTY_SOLUTION e INVALID_RUBRIC; indisponibilidade, falha de conexão/autorização/limite/timeout ou resposta inválida do adjudicador quando há critérios pendentes. O motivo exato fica em unscorable_reason. Problema inexistente, assets inválidos e falhas irrecuperáveis anteriores à avaliação preservam os erros HTTP existentes, sem resultado fictício.",
        "Falha técnica isolada do Lean tenta a segunda passagem e mantém needs_review=true. Se o serviço secundário estiver indisponível, a capacidade de produzir a sugestão global fica indisponível mesmo quando existe subtotal conhecido.",
        "", "## Ambiente e verificação", "", f"Branch: {state['branch']}; HEAD: {state['head']}.",
        f"Git diff SHA-256: {state['git_diff_sha256']}.", f"Testes: {test_summary}.",
        "Seleção exatamente igual à anterior; textos originais; 18 auditorias sequenciais. Nenhum batch de 502/1.000.",
        "", "## Antes/depois", "", "```json", json.dumps(summary, ensure_ascii=False, indent=2), "```", "",
        "| ID | Antes score | Depois score | Subtotal decidido | Coverage | Pontos estimados | Revisão | Verdict |",
        "|---|---|---|---:|---:|---|---|---|"]
    for key in ids:
        r = new[key]
        lines.append(f"| {key} | {json.dumps(old[key]['score'])} | {json.dumps(r['score'])} | {r['evaluated_score']} | {r['coverage']:.1%} | {json.dumps(r['estimated_points'])} | {r['needs_review']} | {r['verdict']} |")
    key = "ITA2025F2Q5_S003_L04"
    r = new[key]
    lines += ["", "## Regressão F2Q5", "", f"{key}: score={r['score']}, coverage={r['coverage']}, estimated_points={r['estimated_points']}.", ""]
    for item in r["rubric_assessment"]["items"]:
        lines.append(f"- {item['id']}: status={item['mathematical_status']}; points={item['points']}; suggested_points={item['suggested_points']}; basis={item['scoring_basis']}.")
        if item["scoring_basis"] == "secondary_adjudication":
            lines.append("  Evidência: " + json.dumps(item["scoring_evidence"], ensure_ascii=False))
            lines.append("  Justificativa: " + item["scoring_rationale"])
    lines += ["", "## Limitações", "",
        "Pontuação secundária é uma estimativa semântica sujeita a erro e dependente de serviço externo; não prova matemática. needs_review permanece explícito mesmo com score máximo ou zero. Descrições de critérios determinam o julgamento e as pautas atuais não codificam parciais.",
        "A divergência F2Q1 a,b, os casos zero claims, o extractor F2Q5 e o timeout Lean não foram corrigidos. Refutações emitidas pelo fluxo atual são preservadas, inclusive quando a extração merece inspeção posterior.",
        "As escalas/rubricas não são diretamente comparáveis: não foram calculados acurácia, MAE ou erro contra nota_final sintética.", ""]
    (after / "SCORE_POLICY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--test-summary", default="Consulte o registro de testes da entrega")
    args = parser.parse_args()
    compare(args.before, args.after, args.test_summary)
