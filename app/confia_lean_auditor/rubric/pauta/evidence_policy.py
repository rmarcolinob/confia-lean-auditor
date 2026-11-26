"""Explicit experimental evidence acceptance; no scoring rules or LLM imports."""
from dataclasses import dataclass


@dataclass(frozen=True)
class HybridEvidencePolicy:
    version: str = 'tme-hybrid-evidence.v1'

    def accepts(self, evidence):
        m = evidence.metadata
        return (evidence.origin == 'semantic' and evidence.verification_source == 'semantic'
                and evidence.status == 'supported' and evidence.attributable_to_student
                and evidence.grounding_status == 'grounded' and bool(evidence.evidence_refs)
                and m.get('reconciliation_policy') == self.version
                and m.get('evidence_tier') == 'SEMANTIC_SUPPORTED'
                and m.get('context_valid') is True and not m.get('conflict')
                and m.get('confidence') in {'high', 'medium', 'low'})

    def needs_review(self, decision):
        if decision.metadata.get('conflict'):
            return True
        if decision.effective_status not in {'supported', 'refuted'}:
            return False
        if decision.origin == 'semantic':
            return not (self.accepts_decision(decision) and decision.metadata.get('confidence') == 'high')
        return decision.origin in {'secondary', 'diagram'}

    def accepts_decision(self, decision):
        return (decision.verification_source == 'semantic'
                and decision.grounding_status == 'grounded'
                and decision.metadata.get('reconciliation_policy') == self.version
                and decision.metadata.get('evidence_tier') == 'SEMANTIC_SUPPORTED'
                and decision.metadata.get('context_valid') is True)
