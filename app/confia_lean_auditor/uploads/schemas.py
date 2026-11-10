from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from confia_lean_auditor.capture.schemas import Identifier

MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_FILE_BASE64 = ((MAX_FILE_BYTES + 2) // 3) * 4
MAX_REQUEST_BYTES = 3 * MAX_FILE_BASE64 + 64 * 1024
MAX_FILES = 3


class UploadModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class UploadFilePayload(UploadModel):
    filename: Optional[str] = Field(default=None, max_length=200)
    data_base64: str = Field(min_length=1, max_length=MAX_FILE_BASE64)


class UploadAnswersRequest(UploadModel):
    problem_id: Identifier
    files: list[UploadFilePayload] = Field(min_length=1, max_length=MAX_FILES)


class UploadedPage(UploadModel):
    page_index: int = Field(ge=0)
    source_file_index: int = Field(ge=0)
    source_filename: Optional[str] = None
    source_media_type: Literal["image/png", "image/jpeg", "application/pdf"]
    page_in_source: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    latency_ms: float = Field(ge=0)
    truncated: bool
    answer_text: str


class RemovedText(UploadModel):
    kind: Literal["before_statement", "statement"]
    page_index: int = Field(ge=0)
    text: str


class UploadAnswersResponse(UploadModel):
    upload_id: str = Field(pattern=r"^upl_[0-9a-f]{32}$")
    problem_id: str
    status: Literal["NEEDS_REVIEW"] = "NEEDS_REVIEW"
    answer_text: str
    statement_found: bool
    statement_match: Optional[float] = None
    pages: list[UploadedPage]
    removed: list[RemovedText]
    warnings: list[str]
    provider: Literal["glm_ocr"] = "glm_ocr"
    adapter: str
    adapter_version: str
    parameters: dict[str, Union[str, int, float, bool, None]]
    created_at: datetime
