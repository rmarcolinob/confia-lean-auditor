from __future__ import annotations

import copy
import json

import pytest
from pydantic import ValidationError

from confia_lean_auditor.capture.schemas import (
    MAX_IMPORT_BYTES,
    CaptureDocument,
    validate_capture_json,
)


def valid_document() -> dict:
    return {
        "schema_version": "1.0",
        "document_kind": "draft",
        "draft_id": "draft:test-1",
        "local_snapshot_id": None,
        "problem_id": "ITA2025F2Q1",
        "input_mode": "tablet_ink",
        "origin": "experimental_local",
        "pages": [
            {
                "page_id": "page:1",
                "index": 0,
                "logical_width": 1200,
                "logical_height": 1600,
                "coordinate_system": "top_left_css_pixels",
            }
        ],
        "strokes": [
            {
                "stroke_id": "stroke:1",
                "page_id": "page:1",
                "pointer_type": "pen",
                "color": "#17355c",
                "width": 4,
                "interrupted": False,
                "points": [
                    {"x": 10, "y": 20, "t_ms": 0, "pressure_reported": 0.2},
                    {"x": 40, "y": 50, "t_ms": 8, "pressure_reported": 0.6},
                ],
            }
        ],
        "operations": [
            {
                "operation_id": "operation:add-1",
                "kind": "add",
                "stroke_id": "stroke:1",
                "target_operation_id": None,
                "client_time": "2026-09-30T12:00:00Z",
            }
        ],
        "active_stroke_ids": ["stroke:1"],
        "renderer": {
            "renderer": "confia_canvas_polyline",
            "renderer_version": "1.0.0",
            "pressure_used_for_width": False,
            "line_cap": "round",
            "line_join": "round",
            "png_background": "#ffffff",
            "png_includes_grid": False,
        },
        "client_created_at": "2026-09-30T12:00:00Z",
        "client_updated_at": "2026-09-30T12:01:00Z",
    }


def test_valid_capture_document_and_round_trip_preserve_data():
    payload = valid_document()
    document = CaptureDocument.model_validate(payload)
    round_trip = CaptureDocument.model_validate_json(document.model_dump_json())

    assert round_trip == document
    assert round_trip.model_dump(mode="json") == CaptureDocument.model_validate(payload).model_dump(mode="json")


def test_extra_fields_are_forbidden_at_every_level():
    payload = valid_document()
    payload["server_receipt_id"] = "invented"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CaptureDocument.model_validate(payload)

    payload = valid_document()
    payload["strokes"][0]["biometric_identity"] = "invented"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CaptureDocument.model_validate(payload)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numbers_are_rejected(value: float):
    payload = valid_document()
    payload["strokes"][0]["points"][0]["x"] = value
    with pytest.raises(ValidationError, match="finite"):
        CaptureDocument.model_validate(payload)


def test_duplicate_ids_are_rejected():
    payload = valid_document()
    second = copy.deepcopy(payload["strokes"][0])
    payload["strokes"].append(second)
    with pytest.raises(ValidationError, match="stroke IDs must be unique"):
        CaptureDocument.model_validate(payload)


def test_unknown_references_and_inconsistent_active_state_are_rejected():
    payload = valid_document()
    payload["operations"][0]["stroke_id"] = "stroke:missing"
    with pytest.raises(ValidationError, match="unknown stroke"):
        CaptureDocument.model_validate(payload)

    payload = valid_document()
    payload["active_stroke_ids"] = []
    with pytest.raises(ValidationError, match="does not match"):
        CaptureDocument.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("x", 1201, "outside page"),
        ("y", -1, "outside page"),
        ("pressure_reported", 1.1, "less than or equal to 1"),
    ],
)
def test_point_bounds_are_rejected(field: str, value: float, message: str):
    payload = valid_document()
    payload["strokes"][0]["points"][0][field] = value
    with pytest.raises(ValidationError, match=message):
        CaptureDocument.model_validate(payload)


def test_decreasing_point_times_are_rejected():
    payload = valid_document()
    payload["strokes"][0]["points"][1]["t_ms"] = -0.1
    with pytest.raises(ValidationError):
        CaptureDocument.model_validate(payload)

    payload = valid_document()
    payload["strokes"][0]["points"][1]["t_ms"] = 0
    payload["strokes"][0]["points"][0]["t_ms"] = 1
    with pytest.raises(ValidationError, match="non-decreasing"):
        CaptureDocument.model_validate(payload)


def test_page_limit_and_indices_are_enforced():
    payload = valid_document()
    for index in (1, 2, 3):
        page = copy.deepcopy(payload["pages"][0])
        page["page_id"] = f"page:{index + 1}"
        page["index"] = index
        payload["pages"].append(page)
    with pytest.raises(ValidationError):
        CaptureDocument.model_validate(payload)


def test_undo_and_redo_references_reconstruct_the_active_state():
    payload = valid_document()
    payload["operations"].extend(
        [
            {
                "operation_id": "operation:undo-1",
                "kind": "undo",
                "stroke_id": "stroke:1",
                "target_operation_id": "operation:add-1",
                "client_time": "2026-09-30T12:02:00Z",
            },
            {
                "operation_id": "operation:redo-1",
                "kind": "redo",
                "stroke_id": "stroke:1",
                "target_operation_id": "operation:undo-1",
                "client_time": "2026-09-30T12:03:00Z",
            },
        ]
    )
    assert CaptureDocument.model_validate(payload).active_stroke_ids == ["stroke:1"]

    payload["operations"][-1]["target_operation_id"] = "operation:add-1"
    with pytest.raises(ValidationError, match="redo must target an undo"):
        CaptureDocument.model_validate(payload)


def test_undo_must_follow_the_reversible_operation_stack():
    payload = valid_document()
    second = copy.deepcopy(payload["strokes"][0])
    second["stroke_id"] = "stroke:2"
    payload["strokes"].append(second)
    payload["operations"].append(
        {
            "operation_id": "operation:add-2",
            "kind": "add",
            "stroke_id": "stroke:2",
            "target_operation_id": None,
            "client_time": "2026-09-30T12:02:00Z",
        }
    )
    payload["operations"].append(
        {
            "operation_id": "operation:bad-undo",
            "kind": "undo",
            "stroke_id": "stroke:1",
            "target_operation_id": "operation:add-1",
            "client_time": "2026-09-30T12:03:00Z",
        }
    )
    payload["active_stroke_ids"] = ["stroke:2"]

    with pytest.raises(ValidationError, match="latest reversible"):
        CaptureDocument.model_validate(payload)


def test_import_size_is_checked_before_json_validation():
    with pytest.raises(ValueError, match="exceeds"):
        validate_capture_json(b"x" * (MAX_IMPORT_BYTES + 1))

    raw = json.dumps(valid_document())
    assert validate_capture_json(raw).problem_id == "ITA2025F2Q1"
