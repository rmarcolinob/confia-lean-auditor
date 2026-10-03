import json
from pathlib import Path
import shutil

from pydantic import ValidationError
import pytest

from benchmarks.handwriting_recognition.loader import load_samples
from benchmarks.handwriting_recognition.metrics import character_error_rate, compare_segments
from benchmarks.handwriting_recognition.runner import run
from benchmarks.handwriting_recognition.schema import RecognitionSample
from confia_lean_auditor.recognition.fake import FakeTestRecognizer
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.recognition.schemas import RecognitionSegment


ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "handwriting_recognition"
MANIFEST = ROOT / "fixtures" / "samples.json"


def segment(value, order=0, kind="math", text=None):
    return RecognitionSegment(page_index=0, order=order, kind=kind, latex=value, text=text)


def test_loader_schema_artificial_samples_and_optional_strokes():
    samples = load_samples(MANIFEST)
    assert len(samples) == 5 and all(s.artificial for s in samples)
    assert [s.sample_id for s in samples] == ["A-preservation", "B-sign", "C-exponent", "D-subscript", "E-missing"]
    optional = samples[0].model_dump()
    optional["input_strokes"] = None
    assert RecognitionSample.model_validate(optional).input_strokes is None
    assert json.loads((ROOT / "sample.schema.json").read_text()) == RecognitionSample.model_json_schema()


@pytest.mark.parametrize("change", ["hash", "traversal", "absolute", "duplicate", "invalid_gold", "symlink", "png", "strokes"])
def test_loader_rejects_invalid_dataset(tmp_path, change):
    target = tmp_path / "fixtures"
    shutil.copytree(MANIFEST.parent, target)
    values = json.loads((target / "samples.json").read_text())
    if change == "hash": values[0]["png"]["sha256"] = "0" * 64
    if change == "traversal": values[0]["png"]["path"] = "../outside.png"
    if change == "absolute": values[0]["png"]["path"] = str(target / "artificial_blank.png")
    if change == "duplicate": values.append(values[0])
    if change == "invalid_gold": values[0]["gold_segments"][0]["page_index"] = 5
    if change == "symlink":
        image = target / "artificial_blank.png"
        image.unlink()
        image.symlink_to(MANIFEST.parent / "artificial_blank.png")
    if change in {"png", "strokes"}:
        from confia_lean_auditor.submissions.store import sha256
        field = "png" if change == "png" else "input_strokes"
        (target / values[0][field]["path"]).write_bytes(b"invalid")
        values[0][field]["sha256"] = sha256(b"invalid")
    (target / "samples.json").write_text(json.dumps(values))
    with pytest.raises((ValueError, ValidationError)):
        load_samples(target / "samples.json")


def test_cer_counts_substitution_insertion_deletion_and_empty_reference():
    assert character_error_rate("abc", "axc") == {"edits": 1, "reference_characters": 3, "rate": 1 / 3}
    assert character_error_rate("abc", "ab") == {"edits": 1, "reference_characters": 3, "rate": 1 / 3}
    assert character_error_rate("abc", "abcd")["edits"] == 1
    assert character_error_rate("", "")["rate"] == 0
    assert character_error_rate("", "x")["rate"] is None


def test_all_required_critical_fixtures_and_transparent_mmer():
    report = run(MANIFEST)
    assert report["mode"] == "fixture_replay"
    rows = {r["sample_id"]: r["metrics"] for r in report["samples"]}
    a = rows["A-preservation"]
    assert a["cer"] == 0 and a["exact_segment_match_rate"] == 1
    assert a["mmer_v0"]["reference_error_rate"] == 0
    assert rows["B-sign"]["critical_sign_mismatch"] == 1
    assert rows["C-exponent"]["exponent_mismatch"] == 1
    assert rows["D-subscript"]["subscript_mismatch"] == 1
    assert rows["E-missing"]["missing_segments"] == 1
    for row in rows.values():
        assert row["mmer_v0"]["scientifically_validated"] is False
        assert row["mmer_v0"]["flagged_reference_segments"] == sum(s["mmer_flagged"] for s in row["segments"])


def test_mixed_channels_extra_segments_whitespace_and_order():
    gold = [segment("x=1", kind="mixed", text="logo")]
    predicted = [segment("x=1", kind="mixed", text="Logo"), segment("y=2", 1)]
    report = compare_segments(gold, predicted)
    assert report["character_edits"] == 4 and report["extra_segments"] == 1
    assert report["exact_segment_matches"] == 0
    assert report["math_symbol_mismatch"] == 0
    assert report["mmer_v0"]["extra_segments"] == 1
    assert compare_segments([segment("x = 1")], [segment("x=1")])["cer"] > 0
    assert compare_segments([segment("x = 1")], [segment("x=1")])["math_symbol_mismatch"] == 0
    assert compare_segments([segment("x=1")], [segment("x=1", 1)])["missing_segments"] == 1
    with pytest.raises(ValueError):
        compare_segments(gold * 2, predicted)


def test_exponent_contiguous_digits_braces_and_subscript_structure():
    assert compare_segments([segment("x^{57}")], [segment("x^{5}7")])["exponent_mismatch"] == 1
    assert compare_segments([segment("a_{n}")], [segment("a n")])["subscript_mismatch"] == 1
    # Signs before an unchanged local exponent must not create an exponent error.
    assert compare_segments([segment("a+x^2")], [segment("a-x^2")])["exponent_mismatch"] == 0


def test_runner_can_use_explicit_local_registry_without_any_external_provider():
    registry = RecognizerRegistry()
    registry.register("fake_test", FakeTestRecognizer)
    report = run(MANIFEST, "fake_test", registry)
    assert report["mode"] == "adapter" and report["provider"] == "fake_test" and report["sample_count"] == 5
    assert report["samples"][0]["metrics"]["exact_segment_matches"] == 1


def test_missing_unsigned_math_is_not_a_sign_mismatch():
    report = compare_segments([segment("x=1")], [])
    assert report["missing_segments"] == 1 and report["math_symbol_mismatch"] == 1
    assert report["critical_sign_mismatch"] == 0
