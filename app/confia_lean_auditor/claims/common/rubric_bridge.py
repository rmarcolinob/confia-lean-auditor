"""Runtime student evidence for explicit, criterion-complete obligations.

Expected objects stay references. Neither alignment nor a reference theorem is
a student proof. The positive gate still owns every required microclaim.
"""
from confia_lean_auditor.core.schemas import ExtractedClaim
from confia_lean_auditor.rubric.positive_evidence import rules, related_check_types
from confia_lean_auditor.student_claims.grounding import local_integer_bindings, source_matches
from confia_lean_auditor.student_claims.schemas import is_mathematically_refuted
from .adapters import claim_from_extracted, claim_from_student, payload_copy
from .alignment import align_claims, align_obligations
from .expected import explicit_obligations, annotate
from .bridges import matching_student_check
from .canonical import PAIRS


class RubricClaimContext:
    """One invocation's immutable projections and cached alignments, not a score."""

    def __init__(self, *, problem_id, solution_text, extraction, students,
                 checks, rubric_config, statement_text='', correct_answer=None):
        self.problem_id = problem_id
        self.solution_text = solution_text
        self.statement_text = statement_text
        self.checks = tuple(payload_copy(c) for c in checks)
        self.references = tuple(claim_from_extracted(c, problem_id=problem_id,
            solution_text=solution_text, rubric_links=tuple(i.id for i in rubric_config.items
                                                          if i.claim_type == c.type))
            for c in extraction.claims)
        self.students = tuple(claim_from_student(c, solution_text=solution_text,
            statement_text=statement_text, rubric_links=tuple(i.id for i in rubric_config.items
                if payload_copy(c)['claim_type'] in related_check_types(problem_id, i.id)))
            for c in students)
        self.references = tuple(annotate(r, next(i for i in rubric_config.items if i.id==r.rubric_links[0]),
            'existing structured reference payload', statement_text) if len(r.rubric_links)==1 else r
            for r in self.references)
        self._alignments = {}
        self.expected_by_criterion, self.expected_sources = explicit_obligations(
            problem_id=problem_id, solution_text=solution_text, rubric_config=rubric_config,
            correct_answer=correct_answer, statement_text=statement_text)
        # Preserve the historical primary-record accessor; all declared variants
        # participate in matching and evidence, never only the first variant.
        self.expected = {key: records[0] for key, records in self.expected_by_criterion.items()}
        self.expected_records = tuple(r for records in self.expected_by_criterion.values() for r in records)

    def alignment(self, reference):
        if not self._alignments:
            records=(*self.references,*self.expected_records)
            results=align_obligations(records,self.students,solution_text=self.solution_text,
                                     statement_text=self.statement_text)
            self._alignments.update((r.reference_record_id,r) for r in results)
        if reference.record_id not in self._alignments:
            self._alignments[reference.record_id]=align_claims(reference,self.students,
                solution_text=self.solution_text,statement_text=self.statement_text)
        return self._alignments[reference.record_id]

    def evidence(self, item):
        expected = self.expected.get(item.id)
        if expected is None or expected.claim_type != item.claim_type:
            return None
        variants=self.expected_by_criterion[item.id]
        results=[(r,self.alignment(r)) for r in variants]
        adverse=[pair for pair in results if pair[1].status in {'conflicting','ambiguous'}]
        matched=[pair for pair in results if pair[1].status=='aligned']
        if adverse:
            expected,alignment=adverse[0]
        elif matched:
            expected,alignment=matched[0]
            alignment=alignment.model_copy(update={
                'student_record_ids':tuple(dict.fromkeys(s for _,a in matched for s in a.student_record_ids)),
                'preferred_attribution_ids':tuple(dict.fromkeys(s for _,a in matched for s in a.preferred_attribution_ids))})
        else:
            alignment=results[0][1]
        evidence = {'version': 'rubric-student-bridge-v1', 'supported': False,
            'criterion_id': item.id, 'expected_claim_id': expected.record_id,
            'expected_source': self.expected_sources[item.id],
            'expected_claim_ids': [r.record_id for r,a in matched],
            'expected_variants': [{'record_id':r.record_id,'status':a.status,'basis':a.alignment_basis} for r,a in results],
            'alignment': alignment.model_dump(mode='json'),
            'alignment_basis': alignment.alignment_basis, 'student_claim_ids': [],
            'student_check_ids': [], 'verification_basis': None, 'source_spans': [],
            'reason': alignment.reason}
        related_types = set(related_check_types(self.problem_id, item.id))
        related = [c for c in self.checks if c.get('problem_id') == self.problem_id
                   and c.get('claim_type') in related_types]
        if any((c.get('grounding') or {}).get('status') == 'ambiguous' for c in related):
            return {**evidence, 'conflict': True,
                    'reason': 'Student claim interpretation is ambiguous'}
        # A verified claim never silently wins against a grounded refutation,
        # including a component of a composite criterion.
        if any(is_mathematically_refuted(c) and source_matches(c, self.solution_text) for c in related):
            return {**evidence, 'conflict': True,
                    'reason': 'Grounded mathematical refutation takes precedence over student credit'}
        if alignment.status in {'conflicting', 'ambiguous'}:
            return {**evidence, 'conflict': True}
        if alignment.status != 'aligned':
            return evidence
        chosen = [s for s in self.students if s.record_id in alignment.preferred_attribution_ids]
        verified = [c for s in chosen for c in related
            if c.get('status') == 'verified' and c.get('formal_status') in {None, 'verified'}
            and c.get('compiled') is True and c.get('lean_file')
            and c.get('verification_scope') != 'generated_reference'
            and matching_student_check(s, c, solution_text=self.solution_text,
                                       statement_text=self.statement_text)]
        # The independent deterministic route checks the student's value/relation
        # against a trusted, complete declared answer. It is not a claim that
        # canonical equivalence proves arbitrary mathematical statements.
        basis = 'formal_lean_verified' if verified else (
            'deterministic_expected_value' if self.expected_sources[item.id].startswith('problem.')
            else 'deterministic_expected_relation')
        spans = [{'requirement': 'student mathematical obligation',
            'student_claim_id': s.record_id, 'source_text': s.source.raw_text,
            'source_start': s.source.source_start, 'source_end': s.source.source_end,
            'source_sha256': s.source.source_sha256, 'grounding': s.source.model_dump(mode='json'),
            'alignment_basis': alignment.alignment_basis} for s in chosen]
        return {**evidence, 'supported': True, 'student_claim_ids': [s.record_id for s in chosen],
                'student_check_ids': list(dict.fromkeys(c['id'] for c in verified)),
                'verification_basis': basis, 'source_spans': spans,
                'reason': 'Grounded student content satisfies the explicit mathematical obligation'}
