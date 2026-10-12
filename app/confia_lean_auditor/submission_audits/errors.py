"""Safe domain categories; never include persisted values in diagnostics."""


class AuditConflict(ValueError):
    code = "AUDIT_RUN_CONFLICT"
    message = "Não foi possível recuperar esta análise. Atualize a solução ou execute uma nova análise."


class UnacceptedSource(AuditConflict):
    code = "TRANSCRIPTION_NOT_ACCEPTED"
    message = "A transcrição precisa ser conferida antes da análise."


class SourceIntegrityError(AuditConflict):
    code = "SOURCE_INTEGRITY_MISMATCH"
    message = "A fonte desta análise não passou na verificação de integridade."


class ResultIntegrityError(AuditConflict):
    code = "RESULT_INTEGRITY_MISMATCH"
    message = "Não foi possível validar a integridade do resultado desta análise."


class RevisionConflict(AuditConflict):
    code = "REVISION_CONFLICT"
    message = "A revisão solicitada não corresponde ao aceite. Atualize a solução."
