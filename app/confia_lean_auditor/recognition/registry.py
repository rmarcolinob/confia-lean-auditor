"""Explicit factories; provider-specific choices belong only to registered adapters."""
from dataclasses import dataclass
import os
from typing import Callable, Protocol, Optional, Union

from confia_lean_auditor.recognition.schemas import InputMode, ProviderOutput
from confia_lean_auditor.recognition.execution import ProviderDeadline


@dataclass(frozen=True)
class RecognitionArtifact:
    filename: str
    page_index: Optional[int]
    sha256: str
    data: bytes


@dataclass(frozen=True)
class RecognitionInput:
    submission_id: str
    artifacts: tuple[RecognitionArtifact, ...]
    deadline: Optional[ProviderDeadline] = None


class Recognizer(Protocol):
    provider: str
    display_label: str
    adapter: str
    adapter_version: str
    input_mode: InputMode
    # Declare only a public allowlist; configuration/credentials stay inside the adapter.
    public_parameters: dict[str, Union[str, int, float, bool, None]]

    def recognize(self, source: RecognitionInput) -> ProviderOutput: ...


class UnknownRecognizer(ValueError):
    pass


class RecognizerRegistry:
    def __init__(self):
        self._factories: dict[str, Callable[[], Recognizer]] = {}

    def register(self, provider: str, factory: Callable[[], Recognizer]):
        if provider in self._factories:
            raise ValueError("provider already registered")
        self._factories[provider] = factory

    def create(self, provider: str) -> Recognizer:
        if provider not in self._factories:
            raise UnknownRecognizer("provider unavailable")
        recognizer = self._factories[provider]()
        if recognizer.provider != provider:
            raise ValueError("factory provider mismatch")
        return recognizer

    def providers(self) -> list[str]:
        return sorted(self._factories)


def configured_registry() -> RecognizerRegistry:
    registry = RecognizerRegistry()
    if os.environ.get("CONFIA_ENV", "production") in {"development", "test"}:
        from confia_lean_auditor.recognition.fake import FakeTestRecognizer
        registry.register("fake_test", FakeTestRecognizer)
    return registry
