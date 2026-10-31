"""Shared assembly of verified facts; no mathematical interpretation or points."""
import hashlib
import json
from confia_lean_auditor.claims.common.schemas import Origin, VerificationLink
from confia_lean_auditor.rubric.pauta.bridge import AuditorFactBundle, FactResult, record_fingerprint


class FactResultsBuilder:
    def __init__(self, digital, solution_id, *, problem_id, checker_version):
        self.digital, self.solution_id = digital, solution_id
        self.problem_id, self.checker_version = problem_id, checker_version
        self.records = {r.record_id: r for r in digital.records}
        self.pending = []

    def add(self, fact_id, records, value, *, mechanism="deterministic", metadata=None, check=None):
        ids = tuple(dict.fromkeys(r.record_id for r in records))
        status = value if isinstance(value, str) else ("verified" if value else "refuted")
        token = hashlib.sha256(json.dumps([self.solution_id, fact_id, ids, status,
            mechanism, metadata], sort_keys=True).encode()).hexdigest()[:20]
        link = VerificationLink(verification_id=f"{self.checker_version}:{token}",
            mechanism="student_check", origin=Origin.STUDENT_EXPLICIT,
            status=status, attributed_to_student=True,
            artifact_ref=(check.get("refutation_lean_file") if status == "refuted" else check.get("lean_file"))
            if check and (check.get("lean_file") or check.get("refutation_lean_file")) else f"check:{token}")
        self.pending.append(dict(fact_id=fact_id, source_claim_ids=ids, verification=link,
            verification_source=mechanism, metadata={"checker": self.checker_version, **(metadata or {})},
            student_check=check))

    def finish(self):
        for entry in self.pending:
            for identifier in entry["source_claim_ids"]:
                record = self.records[identifier]
                self.records[identifier] = record.model_copy(update={"verification_results":
                    (*record.verification_results, entry["verification"])})
        facts = tuple(FactResult(**entry, record_fingerprints={i: record_fingerprint(self.records[i])
            for i in entry["source_claim_ids"]}) for entry in self.pending)
        return AuditorFactBundle(problem_id=self.problem_id, solution_id=self.solution_id,
            source_sha256=hashlib.sha256(self.digital.source_text.encode()).hexdigest(),
            records=tuple(self.records.values()), facts=facts)
