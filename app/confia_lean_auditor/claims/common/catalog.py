"""Compact claim/verification/rubric joins for local artifacts, not grading."""
from confia_lean_auditor.rubric.positive_evidence import related_check_types
from .adapters import claim_from_extracted, claim_from_student, payload_copy, record_id, source_digest
from .alignment import align_claims
from .bridges import matching_student_check
from .schemas import CriterionTrace, MathClaimCatalog, Origin, VerificationLink


def build_claim_catalog(*, problem_id, solution_text, extraction, students, checks,
                        rubric_config, rubric, formal_steps=(), microclaims=(), statement_text='',
                        claim_context=None):
    records = []
    prepared = {r.record_id: r for r in (*claim_context.references, *claim_context.students)} if claim_context else {}
    for claim in extraction.claims:
        links = tuple(item.id for item in rubric_config.items if item.claim_type == claim.type)
        record = prepared.get(record_id('extracted', claim.id))
        if record is None:
            record = claim_from_extracted(claim, problem_id=problem_id, solution_text=solution_text, rubric_links=links)
        verifications = []
        for index, step in enumerate(formal_steps):
            if claim.type in step.supports_claim_types:
                verifications.append(VerificationLink(verification_id=step.id, mechanism='formal_step',
                    origin=Origin.GENERATED_REFERENCE, status=step.status, artifact_ref=f'audit.json#/formal_steps/{index}'))
        for index, microclaim in enumerate(microclaims):
            if claim.type in microclaim.claim_types:
                verifications.append(VerificationLink(verification_id=microclaim.id, mechanism='microclaim',
                    origin=Origin.GENERATED_REFERENCE, status=microclaim.lean_status,
                    artifact_ref=f'audit.json#/microclaims/{index}'))
        for index, item in enumerate(rubric.items):
            if item.id in links and item.claim_id == claim.id and item.positive_evidence is not None:
                verifications.append(VerificationLink(verification_id=f'positive:{item.id}',
                    mechanism='positive_evidence_gate', origin=Origin.REFERENCE_EXPECTED,
                    status='supported' if item.positive_evidence.get('supported') else 'indeterminate',
                    artifact_ref=f'audit.json#/rubric_assessment/items/{index}/positive_evidence'))
        records.append(record.model_copy(update={'verification_results': tuple(verifications)}))
    for student in students:
        payload = payload_copy(student)
        links = tuple(item.id for item in rubric_config.items
                      if payload['claim_type'] in related_check_types(problem_id, item.id))
        record = prepared.get(record_id('student', payload['id']))
        if record is None:
            record = claim_from_student(student, solution_text=solution_text,
                                        statement_text=statement_text, rubric_links=links)
        verifications = []
        for index, check in enumerate(checks):
            data = payload_copy(check)
            if all(data.get(k) == payload.get(k) for k in ('id', 'problem_id', 'claim_type', 'data')):
                verifications.append(VerificationLink(verification_id=data['id'], mechanism='student_check',
                    origin=record.provenance.origin, status=data['status'],
                    attributed_to_student=matching_student_check(record, check, solution_text=solution_text,
                                                                   statement_text=statement_text),
                    artifact_ref=f'audit.json#/student_claim_checks/{index}'))
        records.append(record.model_copy(update={'verification_results': tuple(verifications)}))
    if claim_context:
        records.extend(claim_context.expected_records)
    student_records = [r for r in records if r.provenance.channel == 'student']
    reference_records = [r for r in records if r.provenance.channel == 'extracted']
    alignments = tuple(claim_context.alignment(r) if claim_context else
                       align_claims(r, student_records, solution_text=solution_text,
                                    statement_text=statement_text) for r in reference_records)
    configs = {item.id: item for item in rubric_config.items}
    reference_ids = {r.record_id for r in reference_records}
    traces = []
    for index, item in enumerate(rubric.items):
        reference = record_id('extracted', item.claim_id) if item.claim_id is not None else None
        bridge = (item.positive_evidence or {}).get('student_bridge', {})
        if bridge.get('supported'):
            reference = bridge['expected_claim_id']
        attributed_ids = bridge.get('student_claim_ids', ()) if bridge.get('supported') else ()
        traces.append(CriterionTrace(criterion_id=item.id,
            reference_record_id=reference if reference in reference_ids else None,
            student_record_ids=tuple(r.record_id for r in student_records
                if item.id in r.rubric_links or r.record_id in attributed_ids),
            required_microclaim_ids=tuple(configs[item.id].required_microclaim_ids),
            scoring_basis=item.scoring_basis, decision_ref=f'audit.json#/rubric_assessment/items/{index}',
            evidence_ref=f'audit.json#/rubric_assessment/items/{index}/positive_evidence'))
    return MathClaimCatalog(problem_id=problem_id, source_sha256=source_digest(solution_text),
                            records=tuple(records), alignments=alignments, criterion_traces=tuple(traces))
