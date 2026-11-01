"""Persisted TME result, embedding the unmodified mathematical contracts."""
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from confia_lean_auditor.rubric.pauta.models import PautaAssessment, PautaConfig
from confia_lean_auditor.rubric.pauta.bridge import PautaBridgeResult

PUBLIC_PROBLEMS = {f'TME2026P{n}': ('TME2_P1_PILOT' if n == 1 else f'TME2026P{n}') for n in range(1, 6)}


class TMEAuditContext(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    auditor_version: str
    pauta_version: str
    pauta_sha256: str
    use_lean: bool


class TMEAuditResult(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    schema_version: Literal['tme-audit-result.v1'] = 'tme-audit-result.v1'
    problem_id: str
    accepted_transcription_revision_id: str
    accepted_revision_sha256: str
    context: TMEAuditContext
    artifact_dir: str
    pauta: PautaConfig
    bridge: PautaBridgeResult
    assessment: PautaAssessment
    input_warnings: list[str]
    # Explicit absence of the ITA reproducibility manifest; the TME context,
    # source, result and mandatory artifact digests are persisted by AuditRun.
    reproducibility: None = None

    @computed_field
    @property
    def score(self) -> Optional[float]:
        return float(self.assessment.score) if self.assessment.score is not None else None

    @computed_field
    @property
    def max_score(self) -> float:
        return float(self.assessment.max_score)

    @computed_field
    @property
    def needs_review(self) -> bool:
        return self.assessment.needs_review

    @computed_field
    @property
    def verdict(self) -> str:
        return 'inconclusivo' if self.needs_review else 'concluido'

    @model_validator(mode='before')
    @classmethod
    def validate_projection(cls, value):
        # Computed API fields are checked, never trusted as a second scoring policy.
        if isinstance(value, dict):
            value = dict(value)
            if value.get('schema_version') not in (None, 'tme-audit-result.v1') or 'assessment' not in value:
                raise ValueError('Not a TME result')
            a = PautaAssessment.model_validate(value['assessment'])
            expected = dict(score=float(a.score) if a.score is not None else None,
                            max_score=float(a.max_score), needs_review=a.needs_review,
                            verdict='inconclusivo' if a.needs_review else 'concluido')
            for key, expected_value in expected.items():
                if key in value and value.pop(key) != expected_value:
                    raise ValueError('TME score projection changed')
        return value

    @model_validator(mode='after')
    def bindings(self):
        from confia_lean_auditor.rubric.pauta.engine import PautaEngine
        if PUBLIC_PROBLEMS.get(self.problem_id) != self.pauta.problem_id:
            raise ValueError('TME problem binding mismatch')
        if self.assessment != PautaEngine().evaluate(self.pauta, self.bridge.evidence):
            raise ValueError('TME assessment binding mismatch')
        if (self.context.pauta_sha256 != self.assessment.config_sha256
                or self.context.pauta_version != self.assessment.pauta_version
                or self.bridge.auditor.problem_id != self.pauta.problem_id):
            raise ValueError('TME pauta binding mismatch')
        return self
