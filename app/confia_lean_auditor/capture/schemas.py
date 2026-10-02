from __future__ import annotations

import math
from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


SCHEMA_VERSION = "1.0"
MAX_PAGES = 3
MAX_STROKES = 2_000
MAX_POINTS_PER_STROKE = 20_000
MAX_TOTAL_POINTS = 200_000
MAX_OPERATIONS = 10_000
MAX_LOGICAL_SIDE = 8_192
MAX_IMPORT_BYTES = 10 * 1024 * 1024

Identifier = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$"),
]


class CaptureModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CapturePoint(CaptureModel):
    x: float
    y: float
    t_ms: float = Field(ge=0)
    pressure_reported: Optional[float] = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_finite_values(self) -> "CapturePoint":
        values = (self.x, self.y, self.t_ms)
        if self.pressure_reported is not None:
            values += (self.pressure_reported,)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("point values must be finite")
        return self


class CapturePage(CaptureModel):
    page_id: Identifier
    index: int = Field(ge=0, lt=MAX_PAGES)
    logical_width: float = Field(gt=0, le=MAX_LOGICAL_SIDE)
    logical_height: float = Field(gt=0, le=MAX_LOGICAL_SIDE)
    coordinate_system: Literal["top_left_css_pixels"] = "top_left_css_pixels"

    @model_validator(mode="after")
    def validate_finite_dimensions(self) -> "CapturePage":
        if not math.isfinite(self.logical_width) or not math.isfinite(self.logical_height):
            raise ValueError("page dimensions must be finite")
        return self


class CaptureStroke(CaptureModel):
    stroke_id: Identifier
    page_id: Identifier
    pointer_type: Literal["pen", "mouse"]
    color: Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$")] = "#17355c"
    width: float = Field(gt=0, le=64)
    interrupted: bool = False
    points: list[CapturePoint] = Field(min_length=1, max_length=MAX_POINTS_PER_STROKE)

    @model_validator(mode="after")
    def validate_stroke(self) -> "CaptureStroke":
        if not math.isfinite(self.width):
            raise ValueError("stroke width must be finite")
        previous = -1.0
        for point in self.points:
            if point.t_ms < previous:
                raise ValueError("point times must be non-decreasing")
            previous = point.t_ms
        return self


class CaptureOperation(CaptureModel):
    operation_id: Identifier
    kind: Literal["add", "erase", "undo", "redo"]
    stroke_id: Identifier
    target_operation_id: Optional[Identifier] = None
    client_time: datetime

    @model_validator(mode="after")
    def validate_target_shape(self) -> "CaptureOperation":
        if self.kind in {"add", "erase"} and self.target_operation_id is not None:
            raise ValueError("add/erase operations cannot have a target operation")
        if self.kind in {"undo", "redo"} and self.target_operation_id is None:
            raise ValueError("undo/redo operations require a target operation")
        return self


class RendererConfig(CaptureModel):
    renderer: Literal["confia_canvas_polyline"] = "confia_canvas_polyline"
    renderer_version: Literal["1.0.0"] = "1.0.0"
    pressure_used_for_width: Literal[False] = False
    line_cap: Literal["round"] = "round"
    line_join: Literal["round"] = "round"
    png_background: Literal["#ffffff"] = "#ffffff"
    png_includes_grid: Literal[False] = False


class CaptureDocument(CaptureModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    document_kind: Literal["draft", "local_snapshot"]
    draft_id: Identifier
    local_snapshot_id: Optional[Identifier] = None
    problem_id: Identifier
    input_mode: Literal["tablet_ink"] = "tablet_ink"
    origin: Literal["experimental_local"] = "experimental_local"
    pages: list[CapturePage] = Field(min_length=1, max_length=MAX_PAGES)
    strokes: list[CaptureStroke] = Field(default_factory=list, max_length=MAX_STROKES)
    operations: list[CaptureOperation] = Field(default_factory=list, max_length=MAX_OPERATIONS)
    active_stroke_ids: list[Identifier] = Field(default_factory=list)
    renderer: RendererConfig = Field(default_factory=RendererConfig)
    client_created_at: datetime
    client_updated_at: datetime

    @model_validator(mode="after")
    def validate_document_graph(self) -> "CaptureDocument":
        if self.document_kind == "local_snapshot" and self.local_snapshot_id is None:
            raise ValueError("local snapshots require local_snapshot_id")
        if self.document_kind == "draft" and self.local_snapshot_id is not None:
            raise ValueError("drafts cannot declare local_snapshot_id")
        if self.client_updated_at < self.client_created_at:
            raise ValueError("client_updated_at cannot precede client_created_at")

        page_ids = [page.page_id for page in self.pages]
        if len(page_ids) != len(set(page_ids)):
            raise ValueError("page IDs must be unique")
        page_indices = [page.index for page in self.pages]
        if len(page_indices) != len(set(page_indices)):
            raise ValueError("page indices must be unique")
        if sorted(page_indices) != list(range(len(self.pages))):
            raise ValueError("page indices must be contiguous from zero")
        pages = {page.page_id: page for page in self.pages}

        stroke_ids = [stroke.stroke_id for stroke in self.strokes]
        if len(stroke_ids) != len(set(stroke_ids)):
            raise ValueError("stroke IDs must be unique")
        strokes = {stroke.stroke_id: stroke for stroke in self.strokes}
        total_points = sum(len(stroke.points) for stroke in self.strokes)
        if total_points > MAX_TOTAL_POINTS:
            raise ValueError(f"document exceeds {MAX_TOTAL_POINTS} total points")
        for stroke in self.strokes:
            page = pages.get(stroke.page_id)
            if page is None:
                raise ValueError(f"stroke references unknown page: {stroke.page_id}")
            for point in stroke.points:
                if point.x < 0 or point.x > page.logical_width:
                    raise ValueError(f"point x is outside page {page.page_id}")
                if point.y < 0 or point.y > page.logical_height:
                    raise ValueError(f"point y is outside page {page.page_id}")

        operation_ids = [operation.operation_id for operation in self.operations]
        if len(operation_ids) != len(set(operation_ids)):
            raise ValueError("operation IDs must be unique")

        prior_operations: dict[str, CaptureOperation] = {}
        operation_effects: dict[str, bool] = {}
        active: set[str] = set()
        undo_stack: list[str] = []
        redo_stack: list[str] = []
        for operation in self.operations:
            if operation.stroke_id not in strokes:
                raise ValueError(f"operation references unknown stroke: {operation.stroke_id}")
            if operation.kind == "add":
                effect = True
                undo_stack.append(operation.operation_id)
                redo_stack.clear()
            elif operation.kind == "erase":
                effect = False
                undo_stack.append(operation.operation_id)
                redo_stack.clear()
            else:
                target = prior_operations.get(operation.target_operation_id or "")
                if target is None:
                    raise ValueError("undo/redo target must reference a prior operation")
                if target.stroke_id != operation.stroke_id:
                    raise ValueError("undo/redo target must reference the same stroke")
                if operation.kind == "undo":
                    if not undo_stack or operation.target_operation_id != undo_stack[-1]:
                        raise ValueError("undo must target the latest reversible operation")
                    undo_stack.pop()
                    redo_stack.append(operation.operation_id)
                else:
                    if target.kind != "undo":
                        raise ValueError("redo must target an undo operation")
                    if not redo_stack or operation.target_operation_id != redo_stack[-1]:
                        raise ValueError("redo must target the latest undo operation")
                    redo_stack.pop()
                    undo_stack.append(operation.operation_id)
                effect = not operation_effects[target.operation_id]
            if effect:
                active.add(operation.stroke_id)
            else:
                active.discard(operation.stroke_id)
            prior_operations[operation.operation_id] = operation
            operation_effects[operation.operation_id] = effect

        if len(self.active_stroke_ids) != len(set(self.active_stroke_ids)):
            raise ValueError("active stroke IDs must be unique")
        if set(self.active_stroke_ids) != active:
            raise ValueError("active_stroke_ids does not match the operation history")
        return self


def validate_capture_json(raw: str | bytes) -> CaptureDocument:
    size = len(raw.encode("utf-8")) if isinstance(raw, str) else len(raw)
    if size > MAX_IMPORT_BYTES:
        raise ValueError(f"capture document exceeds {MAX_IMPORT_BYTES} bytes")
    return CaptureDocument.model_validate_json(raw)
