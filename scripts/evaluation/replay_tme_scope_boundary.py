"""Offline DEV replay of frozen model/audit outputs, never a new inference.

Only structural gates and downstream reconciliation/scoring are recalculated.
Stored failures stay failures. An old positive gate cannot cover removed selected
evidence; newly eligible obligations without a cached remote decision stay unknown.
Context-only changes are checked by the current deterministic context gate. This
is a conditional replay, not a claim that a model would repeat its old judgment.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

from confia_lean_auditor.rubric.pauta.bridge import PautaBridgeResult
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from confia_lean_auditor.student_claims import hybrid_semantic as semantic
from confia_lean_auditor.student_claims import semantic_sufficiency as sufficiency
from confia_lean_auditor.student_claims.sufficiency_context import annotated_units
from confia_lean_auditor.tme.sufficiency_experiment import reconcile_sufficiency, POLICY

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'artifacts/evaluations/tme_model_ablation_dev25_live_01'
OUTPUT = ROOT / 'artifacts/evaluations/tme_scope_boundary_fix_01'
SCOPE_FILE = 'app/confia_lean_auditor/student_claims/sufficiency_context.py'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def reconcile(row, text, decisions, links):
    evidence, trace = reconcile_sufficiency(
        row['problem_id'], text,
        tuple(semantic.SemanticObligationJudgment.model_validate(j) for j in row['judgments']),
        PautaBridgeResult.model_validate(row['primary_bridge']),
        PautaBridgeResult.model_validate(row['audit_bridge']), decisions, links,
        first_provider_ok=row['first_provider']['status'] == 'completed')
    assessment = PautaEngine().evaluate(semantic.config_for(row['problem_id']), evidence,
                                       evidence_policy=POLICY)
    return dict(evidence=evidence.model_dump(mode='json'), reconciliation=trace,
                potential_assessment=assessment.model_dump(mode='json'))


def authorized_basis_preserved(old, new):
    """Same IDs and every previously judged source span still authorized.

    Restoring a unit's introductory text does not erase the frozen judgment of
    its literal mathematical subspan. Added text never substitutes for an old
    missing span. The current context gate must separately pass.
    """
    if not old or not new or not new['linkage']['valid'] or not new['context']['valid']:
        return False
    old_bindings = {b['evidence_id']: b for b in old['linkage']['bindings']}
    new_bindings = {b['evidence_id']: b for b in new['linkage']['bindings']}
    if old_bindings.keys() != new_bindings.keys():
        return False
    return all(any(q['source_start'] <= p['source_start'] and p['source_end'] <= q['source_end']
                   and q['exact_text'][p['source_start']-q['source_start']:p['source_end']-q['source_start']] == p['exact_text']
                   for q in new_bindings[eid]['authorized_slices'])
               for eid, binding in old_bindings.items() for p in binding['authorized_slices'])


def replay_row(row, text):
    """No provider/auditor calls. All raw responses are validated against OLD input."""
    judgments = tuple(semantic.SemanticObligationJudgment.model_validate(j) for j in row['judgments'])
    old_decisions = tuple(sufficiency.SufficiencyDecision.model_validate(d)
                          for d in row['sufficiency_decisions'])
    old_decision_map = {d.obligation_id: d for d in old_decisions}
    baseline = reconcile(row, text, old_decisions, row['item_linkage'])
    assert baseline['potential_assessment'] == row['potential_assessment'], 'Baseline replay drift'
    assert baseline['evidence'] == row['evidence'], 'Baseline evidence drift'
    old_payload = row['sufficiency_payload']
    meta = row['sufficiency_provider']
    remote = {}
    if meta['status'] == 'completed':
        remote = {d.obligation_id: d for d in sufficiency.validate_response(meta['raw_output'], old_payload)}
    elif meta.get('validation_error'):
        try:
            sufficiency.validate_response(meta['raw_output'], old_payload)
        except ValueError as error:
            assert str(error) == meta['validation_error'], 'Original rejection changed'
        else:
            raise AssertionError('Invalid original response was accepted')
    elif meta['status'] == 'skipped':
        assert not old_payload['obligations']
    old_targets = {t['obligation_id']: t for t in old_payload['obligations']}
    payload, local, links = sufficiency.SemanticSufficiencyGate().prepare(row['problem_id'], text, judgments)
    old_links = {x['obligation_id']: x for x in row['item_linkage']}
    new_links = {x['obligation_id']: x for x in links}
    decisions = list(local)
    provenance = {d.obligation_id: 'current_local_veto' for d in local}
    for target in payload['obligations']:
        oid = target['obligation_id']
        old = old_targets.get(oid)
        cached = remote.get(oid)
        if cached and authorized_basis_preserved(old_links.get(oid), new_links.get(oid)):
            decisions.append(cached)
            provenance[oid] = ('cached_remote_same_input' if old == target
                               else 'cached_remote_preserved_source_spans_new_context_check')
        else:
            failed = meta['status'] == 'unavailable'
            reason = 'provider_error' if failed else 'ambiguous_context'
            fallback = sufficiency.SufficiencyDecision(
                obligation_id=oid, sufficiency='uncertain', evidence_ids=[], reason_code=reason,
                concise_rationale=('Sufficiency provider unavailable or invalid; not a mathematical refutation.' if failed else
                                   'No stored remote decision for this exact selected evidence; offline replay only.'))
            existing = old_decision_map.get(oid)
            decisions.append(existing if failed and existing and existing.reason_code == 'provider_error' else fallback)
            provenance[oid] = ('preserved_provider_failure' if failed else
                               'missing_cached_gate' if not cached else 'changed_selected_evidence')
    result = reconcile(row, text, tuple(decisions), links)
    return dict(solution_id=row['solution_id'], problem_id=row['problem_id'],
                requested_model=row['requested_model'], api_calls=0, shadow=True,
                original_provider_status=meta['status'], decision_provenance=provenance,
                sufficiency_payload=payload, sufficiency_decisions=[d.model_dump(mode='json') for d in decisions],
                item_linkage=links, **result)


def outcome(trace):
    return {k: trace[k] for k in ['decision', 'evidence_tier', 'conflict', 'reason']}


def run():
    pre = read(SOURCE / 'preflight.json')
    assert pre['split'] == 'dev' and pre['cases'] == 25 and pre['holdout_processed'] == 0
    # Never discover or open another data split. The original manifest is the allowlist.
    ids = pre['case_ids']
    manifest = {str(p.relative_to(SOURCE)): digest(p) for p in SOURCE.glob('*.json*')}
    for file, expected in pre['protected_files'].items():
        assert digest(SOURCE / 'execution' / file) == expected
        if file != SCOPE_FILE:
            assert digest(ROOT / file) == expected, f'Protected component changed: {file}'
    spec = importlib.util.spec_from_file_location(
        'confia_lean_auditor.student_claims._frozen_scope', SOURCE / 'execution' / SCOPE_FILE)
    old_scope = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old_scope)
    packets = {sid: read(SOURCE / 'blind_packets' / (sid + '.json')) for sid in ids}
    unit_changes = []
    for sid, packet in packets.items():
        before, after = old_scope.annotated_units(packet['source_text']), annotated_units(packet['source_text'])
        assert len(before) == len(after)
        for a, b in zip(before, after):
            for key in ['evidence_id', 'exact_text', 'source_start', 'source_end', 'context_ids', 'unit_kind']:
                assert a[key] == b[key], (sid, key)
            if a != b:
                unit_changes.append(dict(solution_id=sid, evidence_id=a['evidence_id'], before=a, after=b))
    manual = {(x['solution_id'], x['obligation_id']): x
              for x in read(SOURCE / 'obligation_comparison.json')}
    all_results, differences, scores, metrics = {}, [], [], {}
    for arm in 'ab':
        original = [json.loads(line) for line in (SOURCE / f'model_{arm}.jsonl').read_text().splitlines()]
        assert [r['solution_id'] for r in original] == ids
        results = []
        totals = dict(obligations=0, decision_changes=0, outcome_changes=0, linkage_changes=0,
                      scores_changed=0, false_credits_removed=0, wrong_links_removed=0,
                      legitimate_credits_lost=0, new_supported=0, changed_retained_positive_selection=0,
                      retained_positive_basis_not_preserved=0,
                      new_false_credits=0, new_wrong_links=0)
        for row in original:
            sid = row['solution_id']
            after = replay_row(row, packets[sid]['source_text'])
            results.append(after)
            old_map = {x['obligation_id']: x for x in row['reconciliation']}
            for new in after['reconciliation']:
                oid = new['obligation_id']; old = old_map[oid]
                old_support, new_support = old['decision'] == 'supported', new['decision'] == 'supported'
                review = manual[sid, oid]['arms'][arm]
                status_changed = old['decision'] != new['decision']
                output_changed = outcome(old) != outcome(new)
                link_changed = old['item_linkage'] != new['item_linkage']
                def positive_slices(t):
                    link = (t['item_linkage'] or {}).get('linkage') or {}
                    return [(b['evidence_id'], b['authorized_slices']) for b in link.get('bindings', [])]
                retained_changed = old_support and new_support and positive_slices(old) != positive_slices(new)
                basis_lost = retained_changed and not authorized_basis_preserved(old['item_linkage'], new['item_linkage'])
                totals['obligations'] += 1
                totals['decision_changes'] += status_changed
                totals['outcome_changes'] += output_changed
                totals['linkage_changes'] += link_changed
                totals['new_supported'] += new_support and not old_support
                totals['changed_retained_positive_selection'] += retained_changed
                totals['retained_positive_basis_not_preserved'] += basis_lost
                totals['false_credits_removed'] += review['false_credit'] and not new_support
                totals['wrong_links_removed'] += review['wrong_link'] and not new_support
                totals['legitimate_credits_lost'] += review['legitimate_supported'] and not new_support
                if output_changed or link_changed:
                    differences.append(dict(arm=arm, solution_id=sid, obligation_id=oid,
                        before=outcome(old), after=outcome(new), decision_changed=status_changed,
                        outcome_changed=output_changed, linkage_changed=link_changed,
                        retained_positive_selection_changed=retained_changed,
                        retained_positive_basis_not_preserved=basis_lost,
                        previous_manual_flags={k: review[k] for k in
                            ['false_credit','wrong_link','legitimate_supported','uncertain_supported']},
                        replay_provenance=after['decision_provenance'].get(oid)))
            old_score, new_score = row['potential_assessment']['score'], after['potential_assessment']['score']
            totals['scores_changed'] += old_score != new_score
            scores.append(dict(arm=arm, solution_id=sid, before=old_score, after=new_score,
                               needs_review=after['potential_assessment']['needs_review']))
        # No new support or removal of the previously reviewed positive basis.
        if totals['new_supported'] or totals['retained_positive_basis_not_preserved']:
            totals['new_false_credits'] = totals['new_wrong_links'] = None
        all_results[arm], metrics[arm] = results, totals
    assert all(digest(SOURCE / f) == h for f, h in manifest.items()), 'Frozen artifacts changed'
    decision = ('SCOPE_FIX_GO' if all(m['new_false_credits'] == m['new_wrong_links'] ==
                m['legitimate_credits_lost'] == 0 for m in metrics.values())
                and sum(m['wrong_links_removed'] for m in metrics.values()) > 0 else 'SCOPE_FIX_NO_GO')
    summary = dict(decision=decision, api_calls=0, retries=0, holdout_processed=0, holdout_total=100,
        original_run_sha=pre['git']['sha'], scope_before_sha256=pre['protected_files'][SCOPE_FILE],
        scope_after_sha256=digest(ROOT / SCOPE_FILE), baseline_reproduced=50,
        evidence_units_changed=len(unit_changes), evidence_text_ids_offsets_unchanged=True,
        all_other_protected_components_unchanged=True, metrics=metrics,
        limitations=['Conditional replay of frozen judgments/audits, not a new model evaluation.',
                    'No newly eligible or changed-selection gate result is invented.',
                    'Semantic evaluator hints are unchanged; corrected item_slices are the authoritative scope gate.'])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    def save(name, value):
        (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    for arm, results in all_results.items():
        (OUTPUT / f'replay_{arm}.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in results))
    save('summary.json', summary); save('unit_changes.json', unit_changes)
    save('obligation_changes.json', differences); save('score_comparison.json', scores)
    save('source_manifest.json', manifest)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == '__main__':
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError('Network forbidden during offline scope replay')
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = forbidden
    run()
