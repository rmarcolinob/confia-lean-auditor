"""Opt-in declarative scoring. Existing ITA evaluation is deliberately unchanged."""
import json
from pathlib import Path

from .engine import PautaEngine
from .models import (
    CarryForwardContract, ConditionalContext, ObligationEvidence, PautaAssessment,
    PautaConfig, PautaDecision, PautaEvidence, PautaItem, PautaObligation, PautaRule,
)


def load_pauta(path: Path) -> PautaConfig:
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key in pauta")
            result[key] = value
        return result

    return PautaConfig.model_validate(json.loads(Path(path).read_text(encoding="utf-8"),
                                                object_pairs_hook=unique_keys))


__all__ = ["PautaEngine", "load_pauta", "PautaConfig", "PautaRule", "PautaItem",
           "PautaDecision", "PautaAssessment", "PautaEvidence", "ObligationEvidence",
           "PautaObligation", "CarryForwardContract", "ConditionalContext"]
