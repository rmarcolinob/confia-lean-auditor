"""GLM-OCR served by Ollama. Only this module knows the external API."""
from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from time import perf_counter
from typing import Optional

import httpx

from confia_lean_auditor.recognition.execution import ProviderDeadline

PROMPT = "Text Recognition:"
DEFAULT_MODEL = "glm-ocr"
MAX_OUTPUT_TOKENS = 4096
MAX_RESPONSE_BYTES = 1024 * 1024
logger = logging.getLogger(__name__)


class GlmOcrError(RuntimeError):
    """A fixed, safe category; never include HTTP bodies or manuscript text."""


class GlmOcrNotConfigured(GlmOcrError):
    pass


@dataclass(frozen=True)
class GlmOcrPage:
    text: str
    latency_ms: float
    output_tokens: Optional[int]
    truncated: bool


def configured_base_url() -> Optional[str]:
    url = os.environ.get("CONFIA_GLM_OCR_URL", "").strip().rstrip("/")
    return url or None


class GlmOcrClient:
    provider = "glm_ocr"
    display_label = "GLM-OCR · documento completo"
    adapter = "confia_glm_ocr_ollama"
    adapter_version = "1.0.0"

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, transport=None):
        self.base_url = base_url or configured_base_url()
        self.model = model or os.environ.get("CONFIA_GLM_OCR_MODEL", DEFAULT_MODEL)
        self.transport = transport

    @property
    def public_parameters(self):
        return {"model": self.model, "prompt": PROMPT, "temperature": 0, "max_output_tokens": MAX_OUTPUT_TOKENS}

    def transcribe(self, image_png: bytes, deadline: Optional[ProviderDeadline] = None) -> GlmOcrPage:
        if not self.base_url:
            raise GlmOcrNotConfigured("not_configured")
        remaining = deadline.remaining_seconds() if deadline else 300.0
        if remaining <= 0:
            raise TimeoutError()
        body = json.dumps({
            "model": self.model,
            "prompt": PROMPT,
            "images": [base64.b64encode(image_png).decode()],
            "stream": False,
            "options": {"temperature": 0, "num_ctx": 16384, "num_predict": MAX_OUTPUT_TOKENS},
        }).encode()
        timeout = httpx.Timeout(remaining, connect=min(5.0, remaining), write=min(30.0, remaining))
        started = perf_counter()
        status = failure = None
        try:
            with httpx.Client(timeout=timeout, transport=self.transport, trust_env=False) as client:
                with client.stream("POST", f"{self.base_url}/api/generate", content=body,
                                   headers={"Content-Type": "application/json"}) as response:
                    status = response.status_code
                    if not 200 <= status < 300:
                        raise GlmOcrError("http_4xx" if 400 <= status < 500 else "http_5xx")
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        if deadline and deadline.remaining_seconds() <= 0:
                            raise TimeoutError()
                        size += len(chunk)
                        if size > MAX_RESPONSE_BYTES:
                            raise GlmOcrError("response_too_large")
                        chunks.append(chunk)
            data = json.loads(b"".join(chunks))
            text = data.get("response") if isinstance(data, dict) else None
            if not isinstance(text, str):
                raise GlmOcrError("incomplete_response")
            tokens = data.get("eval_count")
            tokens = tokens if isinstance(tokens, int) and not isinstance(tokens, bool) else None
            truncated = data.get("done_reason") == "length" or (tokens is not None and tokens >= MAX_OUTPUT_TOKENS)
            return GlmOcrPage(text=text.strip(), latency_ms=(perf_counter() - started) * 1000,
                              output_tokens=tokens, truncated=truncated)
        except httpx.TimeoutException:
            failure = "timeout"
            raise TimeoutError() from None
        except httpx.HTTPError:
            failure = "transport_error"
            raise GlmOcrError("transport_error") from None
        except (ValueError, UnicodeDecodeError):
            failure = "invalid_json"
            raise GlmOcrError("invalid_json") from None
        except GlmOcrError as exc:
            failure = str(exc)
            raise
        except TimeoutError:
            failure = "timeout"
            raise
        finally:
            logger.info("glm_ocr_page", extra={
                "provider": self.provider, "status": "success" if failure is None else "failed",
                "http_status": status, "failure_category": failure,
                "duration_ms": round((perf_counter() - started) * 1000, 1)})
