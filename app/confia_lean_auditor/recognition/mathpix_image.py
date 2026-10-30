"""Mathpix v3/text adapter for immutable scan derivations."""
from __future__ import annotations

import json
import logging
import os
import re
from time import perf_counter

import httpx
from pydantic import ValidationError

from confia_lean_auditor.recognition.errors import ProviderFailure
from confia_lean_auditor.recognition.registry import RecognitionInput
from confia_lean_auditor.recognition.schemas import ProviderOutput, RecognitionPageMetadata, RecognitionSegment

ENDPOINT = "https://api.mathpix.com/v3/text"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
logger = logging.getLogger(__name__)


class MathpixImageError(ProviderFailure):
    """Only fixed, non-sensitive categories leave this adapter."""

    def __init__(self, category):
        codes = {
            "not_configured": "PROVIDER_NOT_CONFIGURED", "invalid_input": "INVALID_IMAGE",
            "http_401": "PROVIDER_UNAUTHORIZED", "http_403": "PROVIDER_FORBIDDEN",
            "http_429": "PROVIDER_RATE_LIMITED", "http_5xx": "PROVIDER_UNAVAILABLE",
            "http_4xx": "PROVIDER_REJECTED", "transport_error": "PROVIDER_TRANSPORT_ERROR",
            "response_too_large": "INVALID_PROVIDER_RESPONSE", "invalid_json": "INVALID_PROVIDER_RESPONSE",
            "incomplete_response": "INVALID_PROVIDER_RESPONSE", "unsafe_response": "INVALID_PROVIDER_RESPONSE",
            "invalid_output": "INVALID_PROVIDER_OUTPUT", "unexpected": "PROVIDER_FAILED",
        }
        self.category = category if category in codes else "unexpected"
        super().__init__(codes[self.category])

    def __str__(self):
        return self.category


class MathpixImageProvider:
    provider = "mathpix_image"
    display_label = "Mathpix · imagem da solução"
    adapter = "confia_mathpix_image"
    adapter_version = "1.0.0"
    input_mode = "image"
    public_parameters = {"provider_endpoint": "v3/text", "input_mode": "image",
                         "improve_mathpix": False, "document_layout": True}

    def __init__(self, transport=None):
        self.transport = transport

    def recognize(self, source: RecognitionInput) -> ProviderOutput:
        app_id = os.environ.get("CONFIA_MATHPIX_APP_ID")
        app_key = os.environ.get("CONFIA_MATHPIX_APP_KEY")
        if not app_id or not app_key:
            raise MathpixImageError("not_configured")
        pages = sorted(source.artifacts, key=lambda a: a.page_index if a.page_index is not None else -1)
        if not pages or len(pages) > 3 or [p.page_index for p in pages] != list(range(len(pages))):
            raise MathpixImageError("invalid_input")
        started, status, completed = perf_counter(), None, 0
        segments, metadata, warnings = [], [], []
        failure = None
        try:
            for page in pages:
                mime = ("image/png" if page.data.startswith(b"\x89PNG\r\n\x1a\n") else
                        "image/jpeg" if page.data.startswith(b"\xff\xd8\xff") else None)
                if mime is None or len(page.data) > 8 * 1024 * 1024:
                    raise MathpixImageError("invalid_input")
                remaining = source.deadline.remaining_seconds() if source.deadline else 30.0
                if remaining <= 0:
                    raise TimeoutError()
                timeout = httpx.Timeout(remaining, connect=min(5.0, remaining),
                                        read=min(15.0, remaining), write=min(5.0, remaining))
                options = {"formats": ["text"], "enable_document_layout": True, "rm_spaces": False,
                           "include_line_data": True, "metadata": {"improve_mathpix": False}}
                try:
                    with httpx.Client(timeout=timeout, transport=self.transport, trust_env=False) as client:
                        with client.stream("POST", ENDPOINT,
                                headers={"app_id": app_id, "app_key": app_key},
                                files={"file": (page.filename, page.data, mime)},
                                data={"options_json": json.dumps(options, separators=(",", ":"))}) as response:
                            status = response.status_code
                            if status < 200 or status >= 300:
                                raise MathpixImageError("http_401" if status == 401 else "http_403" if status == 403 else
                                    "http_429" if status == 429 else "http_4xx" if status < 500 else "http_5xx")
                            chunks, size = [], 0
                            for chunk in response.iter_bytes():
                                if source.deadline and source.deadline.remaining_seconds() <= 0:
                                    raise TimeoutError()
                                size += len(chunk)
                                if size > MAX_RESPONSE_BYTES:
                                    raise MathpixImageError("response_too_large")
                                chunks.append(chunk)
                    data = json.loads(b"".join(chunks))
                except httpx.TimeoutException:
                    raise TimeoutError() from None
                except httpx.HTTPError:
                    raise MathpixImageError("transport_error") from None
                except (ValueError, UnicodeDecodeError):
                    raise MathpixImageError("invalid_json") from None
                if not isinstance(data, dict):
                    raise MathpixImageError("incomplete_response")
                # Mathpix also returns HTTP 200 for processing errors. Inspect only
                # its fixed id; never publish error/message/detail from the response.
                if data.get("error") or data.get("error_info"):
                    info = data.get("error_info")
                    error_id = info.get("id") if isinstance(info, dict) else None
                    if error_id is not None and not isinstance(error_id, str):
                        raise MathpixImageError("incomplete_response")
                    if error_id in {"http_unauthorized", "unauthorized_token_request", "account_disabled", "expired_license"}:
                        raise MathpixImageError("http_401")
                    if error_id == "http_max_requests":
                        raise MathpixImageError("http_429")
                    if error_id in {"sys_exception", "connection_closed"}:
                        raise MathpixImageError("http_5xx")
                    if error_id in {"image_decode_error", "image_no_content", "image_not_supported",
                                    "image_max_size", "image_unsupported_content", "math_confidence", "math_syntax"}:
                        raise MathpixImageError("invalid_input")
                    raise MathpixImageError("http_4xx")
                text = data.get("text")
                latex = data.get("latex_styled")
                text = text if isinstance(text, str) and text.strip() else None
                latex = latex if isinstance(latex, str) and latex.strip() else None
                if text is None and latex is None:
                    raise MathpixImageError("incomplete_response")
                if any(secret in value for value in (text, latex) if value for secret in (app_id, app_key)):
                    raise MathpixImageError("unsafe_response")
                # The document text is authoritative. latex_styled is a fallback,
                # never a second copy of the same mathematical work.
                segments.append(RecognitionSegment(page_index=page.page_index, order=0,
                    kind="text" if text else "math", text=text, latex=latex if text is None else None))
                def safe(field, limit):
                    value = data.get(field)
                    return value if (isinstance(value, str) and 0 < len(value) <= limit
                        and re.fullmatch(r"[A-Za-z0-9._:+-]+", value)
                        and app_id not in value and app_key not in value) else None
                metadata.append(RecognitionPageMetadata(page_index=page.page_index,
                    provider_version=safe("version", 80), provider_request_id=safe("request_id", 120),
                    is_handwritten=data.get("is_handwritten") if isinstance(data.get("is_handwritten"), bool) else None))
                if text is None:
                    warnings.append(f"Página {page.page_index + 1}: apenas LaTeX retornado; confira a ordem e os símbolos.")
                completed += 1
            return ProviderOutput(segments=segments, page_metadata=metadata, warnings=warnings,
                provider_version=metadata[0].provider_version if len({p.provider_version for p in metadata}) == 1 else None,
                provider_request_id=metadata[0].provider_request_id if len(metadata) == 1 else None)
        except TimeoutError:
            failure = "timeout"
            raise
        except MathpixImageError as exc:
            failure = str(exc)
            raise
        except ValidationError:
            failure = "invalid_output"
            raise MathpixImageError("invalid_output") from None
        except Exception:
            failure = "unexpected"
            raise MathpixImageError("unexpected") from None
        finally:
            logger.info("recognition_provider", extra={"provider": self.provider,
                "status": "success" if failure is None else "failed", "http_status": status,
                "failure_category": failure, "page_count": len(pages), "completed_pages": completed,
                "duration_ms": round((perf_counter() - started) * 1000, 1)})
