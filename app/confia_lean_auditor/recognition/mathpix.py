"""Mathpix digital-ink adapter. Only this module knows the external API."""
from __future__ import annotations
import json
import logging
import math
import os
import re
from time import perf_counter

import httpx
from pydantic import ValidationError

from confia_lean_auditor.capture.schemas import MAX_TOTAL_POINTS
from confia_lean_auditor.recognition.registry import RecognitionInput
from confia_lean_auditor.recognition.schemas import ProviderOutput, RecognitionPageMetadata, RecognitionSegment
from confia_lean_auditor.submissions.schemas import CaptureSnapshot


ENDPOINT = "https://api.mathpix.com/v3/strokes"
MAX_REQUEST_BYTES = 512 * 1024
MAX_RESPONSE_BYTES = 256 * 1024
logger = logging.getLogger(__name__)


class MathpixProviderError(RuntimeError):
    """A fixed, safe category; never include HTTP bodies or credentials."""


def page_payload(snapshot: CaptureSnapshot, page_index: int) -> tuple[dict, int, int] | None:
    """Preserve stroke and point order; omit deleted strokes and non-ink fields."""
    page = next((page for page in snapshot.pages if page.index == page_index), None)
    if page is None:
        raise MathpixProviderError("invalid_page")
    active = set(snapshot.active_stroke_ids)
    strokes = [stroke for stroke in snapshot.strokes if stroke.stroke_id in active and stroke.page_id == page.page_id]
    if not strokes:
        return None
    if sum(len(stroke.points) for stroke in strokes) > MAX_TOTAL_POINTS:
        raise MathpixProviderError("too_many_points")
    x, y = [], []
    for stroke in strokes:
        xs, ys = [], []
        for point in stroke.points:
            if (not math.isfinite(point.x) or not math.isfinite(point.y)
                    or not 0 <= point.x <= page.logical_width
                    or not 0 <= point.y <= page.logical_height):
                raise MathpixProviderError("invalid_coordinates")
            xs.append(point.x)
            ys.append(point.y)
        x.append(xs)
        y.append(ys)
    payload = {"strokes": {"strokes": {"x": x, "y": y}},
               "metadata": {"improve_mathpix": False}}
    if len(json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()) > MAX_REQUEST_BYTES:
        raise MathpixProviderError("request_too_large")
    return payload, len(strokes), sum(map(len, x))


class MathpixRecognitionProvider:
    provider = "mathpix"
    display_label = "Mathpix · escrita manuscrita"
    adapter = "confia_mathpix_strokes"
    adapter_version = "1.0.0"
    input_mode = "strokes"
    public_parameters = {"provider_endpoint": "v3/strokes", "input_mode": "strokes",
                         "improve_mathpix": False}

    def __init__(self, transport=None):
        self.transport = transport

    def recognize(self, source: RecognitionInput) -> ProviderOutput:
        app_id = os.environ.get("CONFIA_MATHPIX_APP_ID")
        app_key = os.environ.get("CONFIA_MATHPIX_APP_KEY")
        if not app_id or not app_key:
            raise MathpixProviderError("not_configured")
        snapshot_artifacts = [a for a in source.artifacts if a.filename == "snapshot.json"]
        if len(snapshot_artifacts) != 1:
            raise MathpixProviderError("invalid_input")
        try:
            snapshot = CaptureSnapshot.model_validate_json(snapshot_artifacts[0].data)
        except (ValidationError, ValueError):
            raise MathpixProviderError("invalid_input") from None
        pages = [(page.index, page_payload(snapshot, page.index)) for page in sorted(snapshot.pages, key=lambda p: p.index)]
        written = [(index, item) for index, item in pages if item is not None]
        if not written:
            raise MathpixProviderError("empty_ink")
        started = perf_counter()
        completed = 0
        http_status = None
        failure = None
        segments = []
        versions = []
        request_ids = []
        page_metadata = []
        try:
            for index, (payload, _, _) in written:
                remaining = source.deadline.remaining_seconds() if source.deadline else 30.0
                if remaining <= 0:
                    raise TimeoutError()
                timeout = httpx.Timeout(remaining, connect=min(5.0, remaining),
                                        read=min(15.0, remaining), write=min(5.0, remaining))
                try:
                    body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
                    with httpx.Client(timeout=timeout, transport=self.transport, trust_env=False) as client:
                        with client.stream("POST", ENDPOINT, content=body,
                                           headers={"app_id": app_id, "app_key": app_key,
                                                    "Content-Type": "application/json"}) as response:
                            http_status = response.status_code
                            if http_status < 200 or http_status >= 300:
                                category = "http_4xx" if 400 <= http_status < 500 else "http_5xx" if http_status >= 500 else "http_unexpected"
                                raise MathpixProviderError(category)
                            chunks = []
                            size = 0
                            for chunk in response.iter_bytes():
                                if source.deadline and source.deadline.remaining_seconds() <= 0:
                                    raise TimeoutError()
                                size += len(chunk)
                                if size > MAX_RESPONSE_BYTES:
                                    raise MathpixProviderError("response_too_large")
                                chunks.append(chunk)
                    data = json.loads(b"".join(chunks))
                except httpx.TimeoutException:
                    raise TimeoutError() from None
                except httpx.HTTPError:
                    raise MathpixProviderError("transport_error") from None
                except (ValueError, UnicodeDecodeError):
                    raise MathpixProviderError("invalid_json") from None
                if not isinstance(data, dict):
                    raise MathpixProviderError("incomplete_response")
                text = data.get("text")
                latex = data.get("latex_styled")
                if not isinstance(text, str) or not text.strip():
                    text = None
                if not isinstance(latex, str) or not latex.strip():
                    latex = None
                if text is None and latex is None:
                    raise MathpixProviderError("incomplete_response")
                # A provider response is untrusted. Never publish a credential echoed in it.
                if any(secret in value for value in (text, latex) if value is not None for secret in (app_id, app_key)):
                    raise MathpixProviderError("unsafe_response")
                confidence = data.get("confidence")
                if confidence is not None and (not isinstance(confidence, (int, float))
                                               or isinstance(confidence, bool) or not math.isfinite(confidence)
                                               or not 0 <= confidence <= 1):
                    raise MathpixProviderError("invalid_confidence")
                kind = "mixed" if text and latex else "math" if latex else "text"
                segments.append(RecognitionSegment(page_index=index, order=0, kind=kind,
                                                   text=text, latex=latex, confidence=confidence))
                def safe_metadata(field, limit):
                    value = data.get(field)
                    return value if (isinstance(value, str) and value and len(value) <= limit
                                     and re.fullmatch(r"[A-Za-z0-9._:+-]+", value)
                                     and app_id not in value and app_key not in value) else None
                version = safe_metadata("version", 80)
                request_id = safe_metadata("request_id", 120)
                is_handwritten = data.get("is_handwritten")
                if is_handwritten is not None and not isinstance(is_handwritten, bool):
                    raise MathpixProviderError("invalid_metadata")
                page_metadata.append(RecognitionPageMetadata(
                    page_index=index, provider_version=version,
                    provider_request_id=request_id, is_handwritten=is_handwritten))
                if version:
                    versions.append(version)
                if request_id:
                    request_ids.append(request_id)
                completed += 1
            return ProviderOutput(
                provider_version=versions[0] if len(versions) == len(written) and len(set(versions)) == 1 else None,
                provider_request_id=request_ids[0] if len(written) == 1 and len(request_ids) == 1 else None,
                segments=segments,
                page_metadata=page_metadata,
                warnings=["Mathpix não associa o resultado a strokes ou regiões individuais; confira cada página."],
            )
        except TimeoutError:
            failure = "timeout"
            raise
        except MathpixProviderError as exc:
            failure = str(exc)
            raise
        except Exception:
            failure = "unexpected"
            raise MathpixProviderError("unexpected") from None
        finally:
            logger.info("recognition_provider", extra={
                "provider": self.provider, "status": "success" if failure is None else "failed",
                "duration_ms": round((perf_counter() - started) * 1000, 1),
                "page_count": len(written), "completed_pages": completed,
                "stroke_count": sum(item[1] for _, item in written),
                "point_count": sum(item[2] for _, item in written),
                "http_status": http_status, "failure_category": failure,
            })
