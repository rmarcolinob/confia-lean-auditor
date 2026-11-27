"""Scheduling pauses must not invalidate repeated source-bound extraction."""
from unittest.mock import patch
from types import SimpleNamespace
import time

import pytest

from confia_lean_auditor.core.math_canonical import parser
from confia_lean_auditor.student_claims.digital_items import collect_digital_items
from confia_lean_auditor.student_claims import tme2_p3_digital as p3, tme2_p4_digital as p4
from test_tme_accepted_integration import FULL, solution_for, offline, prepare, execute
from test_tme_pilot import setup


def expired_budget(self, depth=0):
    raise parser.Failure('unsupported', 'Canonicalization time budget')


def bounded_extractor(original):
    calls = []

    def extract(problem_id, source):
        calls.append(source)
        if len(calls) > 1:
            # A later wall-clock budget can expire on identical source text.
            # Exercise the real parser's failure path, without sleep or LLMs.
            wall = iter(i * 0.1 for i in range(100000))
            clock = SimpleNamespace(monotonic=lambda: next(wall), thread_time=time.thread_time)
            with patch.object(parser, 'time', clock):
                return original(problem_id, source)
        return original(problem_id, source)

    return extract, calls


@pytest.mark.parametrize('n,module', [(3, p3), (4, p4)])
def test_item_routing_preserves_claims_across_scheduling_pauses(n, module):
    original = getattr(module, f'extract_p{n}_quantities')
    items = solution_for(n, FULL[n])
    expected = collect_digital_items(module.PROBLEM_ID, items, item_ids='abc',
                                    literal_extractors=(original,))
    extract, calls = bounded_extractor(original)
    actual = collect_digital_items(module.PROBLEM_ID, items, item_ids='abc',
                                  literal_extractors=(extract,))
    assert actual == expected
    assert len(calls) > 1
    for record in actual.records:
        if record.provenance.channel == 'native':
            source = record.source
            assert actual.source_text[source.source_start:source.source_end] == source.raw_text
            assert len(record.rubric_links) == 1


@pytest.mark.parametrize('n,module', [(3, p3), (4, p4)])
def test_accepted_audit_survives_descheduling_during_reextraction(offline, monkeypatch, n, module):
    client, calls, _ = offline
    name = f'extract_p{n}_quantities'
    extract, extractions = bounded_extractor(getattr(module, name))
    monkeypatch.setattr(module, name, extract)
    base, _, _, request = prepare(client, n, solution_for(n, FULL[n]))
    run, stored = execute(client, base, request)
    assert run['status'] == 'COMPLETED'
    assert stored.result.score == 20
    assert len(extractions) > 1
    assert calls == []
    # Reading and idempotent retry verify immutable artifacts, not extraction.
    count = len(extractions)
    assert client.post(base + '/audits', json=request).json() == run
    assert len(extractions) == count


def test_timeout_on_initial_extraction_does_not_create_supported_math():
    from confia_lean_auditor.rubric.pauta import load_pauta
    from confia_lean_auditor.rubric.pauta.tme2_p4 import audit_tme2_p4_digital
    from confia_lean_auditor.tme.registry import ROOT
    config = load_pauta(ROOT / 'examples/pautas/tme2_problem4.v1.json')
    with patch.object(parser.Budget, 'tick', expired_budget):
        bridge, assessment = audit_tme2_p4_digital(config, {'a': 'PB: x'}, 'bounded', use_lean=False)
    assert all(e.status == 'indeterminate' for e in bridge.evidence.obligations)
    assert assessment.possible_points > assessment.known_points


def test_parser_still_enforces_actual_cpu_budget(monkeypatch):
    clock = SimpleNamespace(monotonic=lambda: 0, thread_time=lambda: 0)
    monkeypatch.setattr(parser, 'time', clock)
    budget = parser.Budget()
    clock.thread_time = lambda: parser.MAX_SECONDS * 2
    with pytest.raises(parser.Failure) as error:
        budget.tick()
    assert error.value.reason == 'Canonicalization time budget'


def test_parser_does_not_charge_descheduled_time(monkeypatch):
    clock = SimpleNamespace(monotonic=lambda: 0, thread_time=lambda: 0)
    monkeypatch.setattr(parser, 'time', clock)
    budget = parser.Budget()
    clock.monotonic = lambda: 10
    budget.tick()
    assert budget.nodes == 1
