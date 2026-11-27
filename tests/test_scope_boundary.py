"""Structural section boundaries; no model calls or mathematical rejudgment."""
import json
from pathlib import Path

import pytest

from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.student_claims.sufficiency_context import (
    annotated_units, item_regions, link_evidence,
)
from confia_lean_auditor.student_claims.sufficiency_requirements import requirements


@pytest.mark.parametrize('text', [
    '(a) Primeiro.\n(b) Segundo.\n(c) Terceiro.\n(d) Quarto.',
    '  (a)\nPrimeiro.\n\n\t(b) Segundo.\n (c) Terceiro.\n(d) Quarto.',
    '(a) Primeiro.(b) Segundo. (c) Terceiro; (d) Quarto.',
    'a) Primeiro.\r\n B) Segundo.\n c) Terceiro.\n D) Quarto.',
    'Em (a), primeiro. Em (b), segundo. Para (c): terceiro. Para (d): quarto.',
])
def test_real_structural_headings_and_existing_inline_transitions(text):
    assert [r['item_id'] for r in item_regions(text) if r['item_id']] == list('abcd')
    for unit in annotated_units(text):
        for part in unit['item_slices']:
            assert text[part['source_start']:part['source_end']] == part['exact_text']


@pytest.mark.parametrize('reference', [
    'em (c)', 'como em (c)', 'resultado de (c)', 'pelo item (c)',
    'usando (c)', 'de (d)', 'Os valores calculados em (b)',
    'A igualdade obtida para (a)', 'Os dois fatores que aparecem em (c)',
    'O resultado segue de (c), mantendo a soma',
])
@pytest.mark.parametrize('layout', ['(d) Aplicamos {ref} e obtemos 12.',
                                    '(d)\nAplicamos {ref} e obtemos 12.'])
def test_internal_references_keep_the_current_section(reference, layout):
    text = layout.format(ref=reference)
    assert [r['item_id'] for r in item_regions(text)] == ['d']
    assert all(u['item_id'] == 'd' and not u['multiple_items'] for u in annotated_units(text))


def test_reference_does_not_relabel_later_units_or_prevent_next_heading():
    text = '(b) Usamos o resultado obtido em (a).\n\nA soma é 12.\n(c) Outra conta.'
    assert [r['item_id'] for r in item_regions(text)] == ['b', 'c']
    unit = next(u for u in annotated_units(text) if 'A soma' in u['exact_text'])
    assert unit['item_id'] == 'b'


@pytest.mark.parametrize('problem,oid', [
    ('TME2026P1', 'a.identifies_137'), ('TME2026P2', 'a.pair_sum'),
    ('TME2026P3', 'a.bottom_white_count'), ('TME2026P4', 'a.pb'),
    ('TME2026P5', 'a.product'),
])
def test_reference_cannot_authorize_wrong_item_in_any_problem(problem, oid):
    text = '(a) Primeiro resultado.\n(b) O cálculo feito em (a) vale 12.'
    unit = next(u for u in annotated_units(text) if 'O cálculo' in u['exact_text'])
    req = next(r for r in requirements(problem) if r['obligation_id'] == oid)
    link = link_evidence(text, req, [unit['evidence_id']])
    assert unit['item_id'] == 'b'
    assert not link['valid'] and link['rejected'][0]['reason'] == 'wrong_item'


def test_explicit_reference_authorization_is_preserved_without_relabeling():
    text = '(a) AP=6-x.\n(b) Pelo item (a), usamos o valor.'
    unit = next(u for u in annotated_units(text) if u['exact_text'] == 'AP=6-x.')
    req = next(r for r in requirements('TME2026P4') if r['obligation_id'] == 'b.ap')
    link = link_evidence(text, req, [unit['evidence_id']])
    assert [r['item_id'] for r in item_regions(text)] == ['a', 'b']
    assert link['valid'] and link['exceptions'][0]['source_item'] == 'a'
    assert link['exceptions'][0]['authorization'] == 'explicit_textual_reference'


def test_p5_02_exact_frozen_units_keep_ids_text_and_real_origin():
    path = (Path(__file__).resolve().parents[1] / 'artifacts/evaluations'
            '/tme_model_ablation_dev25_live_01/blind_packets/TME2026P5_02.json')
    if not path.exists():
        pytest.skip('Frozen DEV artifact unavailable; never load another dataset')
    packet = json.loads(path.read_text())
    text = packet['source_text']
    original = {u['evidence_id']: u['exact_text'] for u in packet['evidence_units']}
    assert {u.evidence_id: u.exact_text for u in evidence_units(text)} == original
    units = {u['evidence_id']: u for u in annotated_units(text)}
    assert [r['item_id'] for r in item_regions(text)] == list('abcd')
    assert all(units[e]['item_id'] == 'd' for e in ['E016', 'E017', 'E018'])
    assert units['E016']['exact_text'] == original['E016']
    req = next(r for r in packet['requirements'] if r['obligation_id'] == 'c.four_product')
    link = link_evidence(text, req, ['E013', 'E016'])
    assert not link['valid']
    assert link['rejected'] == [{'evidence_id': 'E016', 'reason': 'wrong_item'}]
