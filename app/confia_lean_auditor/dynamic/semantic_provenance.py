"""DYNAMIC-only execution receipts; unknown metadata is never inferred as success."""
from copy import deepcopy
import os

from confia_lean_auditor.semantic_policy.service import SemanticProvider, assess


def assess_with_provenance(request, provider=None):
    actual = provider if provider is not None else SemanticProvider()
    previous_metadata = getattr(actual, 'metadata', None)
    received = False
    unavailable = False

    def invoke(payload):
        nonlocal received, unavailable
        try:
            response = actual(payload)
            received = True
            return response
        except RuntimeError as exc:
            unavailable = isinstance(actual, SemanticProvider) and str(exc) == 'SEMANTIC_PROVIDER_NOT_CONFIGURED'
            raise
        finally:
            metadata = getattr(actual, 'metadata', None)
            # A reused provider may retain the previous response after a timeout.
            # Only metadata published for this invocation can identify its model/receipt.
            if isinstance(metadata, dict) and metadata is not previous_metadata:
                invoke.metadata = deepcopy(metadata)

    trace = assess(request, invoke)
    metadata = trace.get('provider', {})
    standard = isinstance(actual, SemanticProvider)
    has_receipt = standard and bool(metadata.get('response_id'))
    declared_usage = metadata.get('llm_used')
    llm_used = (False if unavailable else declared_usage if type(declared_usage) is bool
                else True if has_receipt else None)
    trace['execution'] = dict(
        stage=request['stage'], adapter=type(actual).__name__, adapter_called=True,
        response_received=received, llm_used=llm_used,
        state='unavailable' if unavailable else 'response_received' if received else 'failed',
        provider=metadata.get('provider') or ('openai' if has_receipt else None),
        requested_model=metadata.get('requested_model') or (
            os.getenv('CONFIA_SEMANTIC_MODEL', 'gpt-6.1-sol') if standard else None),
        model=metadata.get('model') or metadata.get('returned_model'),
        reasoning_effort=metadata.get('reasoning_effort') or (
            os.getenv('CONFIA_SEMANTIC_REASONING_EFFORT', 'medium') if standard else None),
        response_id=metadata.get('response_id'), error_type=trace.get('error_type'),
    )
    return trace


def summarize(traces):
    executions = [t.get('execution', {}) for t in traces]
    usage = [e.get('llm_used') for e in executions]
    result = dict(llm_used=True if any(v is True for v in usage) else
                  None if any(v is None for v in usage) else False)
    for field in ('provider', 'model', 'requested_model', 'reasoning_effort'):
        values = list(dict.fromkeys(e[field] for e in executions if e.get(field) is not None))
        result[field] = values[0] if len(values) == 1 and all(e.get(field) is not None for e in executions) else None
        result[field + '_values'] = values
    return result


def evaluation_record(criterion_id, trace, claim_ids):
    return dict(criterion_id=criterion_id, stage=trace['request']['stage'],
                decision=trace['decision'], execution=deepcopy(trace['execution']),
                claim_ids=list(claim_ids), quotes=deepcopy(trace.get('quotes', [])),
                justification=trace.get('response', {}).get('justification'),
                request_sha256=trace['request_sha256'], response_sha256=trace.get('response_sha256'),
                error_type=trace.get('error_type'), gate_reason=trace.get('gate_reason'))
