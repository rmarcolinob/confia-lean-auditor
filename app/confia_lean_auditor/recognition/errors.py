"""Fixed public error codes; provider text and credentials never cross this boundary."""
from typing import Literal, get_args

RecognitionErrorCode = Literal[
    "PROVIDER_FAILED", "INVALID_PROVIDER_OUTPUT", "PROVIDER_TIMEOUT", "PROVIDER_BUSY",
    "PROVIDER_NOT_CONFIGURED", "PROVIDER_UNAUTHORIZED", "PROVIDER_FORBIDDEN",
    "PROVIDER_RATE_LIMITED", "PROVIDER_UNAVAILABLE", "PROVIDER_TRANSPORT_ERROR",
    "PROVIDER_REJECTED", "INVALID_PROVIDER_RESPONSE", "INVALID_IMAGE",
]


class ProviderFailure(RuntimeError):
    def __init__(self, code: RecognitionErrorCode):
        self.code = code if code in get_args(RecognitionErrorCode) else "PROVIDER_FAILED"
        super().__init__(self.code)
