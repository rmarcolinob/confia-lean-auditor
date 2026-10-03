from typing import Optional

from pydantic import Field, model_validator

from confia_lean_auditor.capture.schemas import Identifier
from confia_lean_auditor.recognition.schemas import RecognitionSegment
from confia_lean_auditor.submissions.schemas import Sha256, SubmissionModel


class SampleArtifact(SubmissionModel):
    path: str = Field(min_length=1, max_length=240)
    sha256: Sha256


class RecognitionSample(SubmissionModel):
    sample_id: Identifier
    artificial: bool = True
    png: SampleArtifact
    input_strokes: Optional[SampleArtifact] = None
    gold_segments: list[RecognitionSegment] = Field(min_length=1, max_length=2_000)
    # Canned output is mandatory only for the offline fixture mode.
    recognized_segments: Optional[list[RecognitionSegment]] = Field(default=None, max_length=2_000)
    description: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def unique_positions(self):
        for segments in (self.gold_segments, self.recognized_segments or []):
            keys = [(s.page_index, s.order) for s in segments]
            if len(keys) != len(set(keys)):
                raise ValueError("duplicate sample segment position")
        return self
