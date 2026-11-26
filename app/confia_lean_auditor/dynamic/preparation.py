"""DY2 lifecycle over the DY1 append-only aggregate; network outside storage locks."""
from datetime import timedelta
from uuid import uuid4
from .models import (DynamicDocument, DynamicEvent, RubricGeneration, SaveRubric, SuggestedRubric, model_sha256)
from .preparation_models import PreparationRecord, PreparationProposal, PreparationReference, SemanticReview
from .provider import OpenAIPreparationProvider, ProviderFailure
from .store import now, DynamicConflict
from .verification import analyze, warning

TERMINAL = {'READY_FOR_REVIEW', 'REVIEW_REQUIRED', 'FAILED'}


class PreparationService:
    def __init__(self, store, provider=None):
        self.store = store
        self.provider = provider or OpenAIPreparationProvider()

    def _event(self, document, preparation, kind, actor, reason=None):
        package = next(p for p in document.packages if p.package_id == preparation.source_package_id)
        return self.store._event(kind, package, actor, now(), reason).model_copy(update={'preparation_id':preparation.preparation_id})

    def _append(self, document, digest, preparation, event, package=None):
        return self.store._append(document.model_copy(update=dict(revision=document.revision+1,
            preparations=(*document.preparations, preparation), events=(*document.events,event),
            **(dict(packages=(*document.packages,package)) if package else {}))), digest)

    def start(self, identifier, request, actor):
        with self.store._locked():
            document, digest = self.store._owned(identifier, actor)
            self.store._expected(document, request)
            old = self.store.latest_preparation(document)
            if old and old.status not in TERMINAL:
                if now() - old.created_at < timedelta(seconds=180):
                    raise DynamicConflict('Preparação já em andamento. Aguarde e recarregue.')
                failed = old.model_copy(update=dict(status='FAILED', completed_at=now(), failure_code='INTERRUPTED_OR_EXPIRED'))
                self._append(document,digest,failed,self._event(document,old,'preparation_failed',actor,'INTERRUPTED_OR_EXPIRED'))
                document,digest = self.store._owned(identifier,actor)
            if old:
                event = self._event(document,old,'preparation_superseded',actor,'REGENERATED')
                self.store._append(document.model_copy(update=dict(revision=document.revision+1,events=(*document.events,event))),digest)
                document,digest = self.store._owned(identifier,actor)
            statement, source = document.statements[-1], document.packages[-1]
            prep = PreparationRecord(preparation_id='dprep_'+uuid4().hex,
                preparation_version=max((p.preparation_version for p in document.preparations),default=0)+1,
                problem_id=identifier, source_package_id=source.package_id,
                statement_version=statement.version_number, statement_sha256=model_sha256(statement),
                status='PENDING', created_at=now(), requested_by=actor.actor_id, reason=request.reason)
            self._append(document,digest,prep,self._event(document,prep,'preparation_pending',actor))
            document,digest = self.store._owned(identifier,actor)
            prep = prep.model_copy(update=dict(status='RUNNING'))
            self._append(document,digest,prep,self._event(document,prep,'preparation_running',actor))
        payload = dict(statement=statement.model_dump(mode='json'), statement_sha256=prep.statement_sha256)
        try:
            proposal, provenance = self.provider.generate('prepare', payload, PreparationProposal)
            proposal = PreparationProposal.model_validate(proposal.model_dump())
            analysis = analyze(proposal)
            prep = prep.model_copy(update=dict(status='READY_FOR_REVIEW' if analysis.trust_state == 'CHECKED_WITHIN_SCOPE' else 'REVIEW_REQUIRED',
                completed_at=now(), proposal=proposal, analysis=analysis, provenance=provenance))
        except Exception as exc:
            prep = prep.model_copy(update=dict(status='FAILED', completed_at=now(),
                failure_code=exc.code if isinstance(exc, ProviderFailure) else 'PREPARATION_INVALID_OUTPUT',
                provenance=exc.provenance if isinstance(exc,ProviderFailure) else None))
        with self.store._locked():
            document,digest = self.store._owned(identifier,actor)
            current_record = next(p for p in reversed(document.preparations) if p.preparation_id == prep.preparation_id)
            if current_record.status != 'RUNNING':
                raise DynamicConflict('Execução expirada; resultado tardio não foi publicado.')
            package = None
            latest = self.store.latest_preparation(document)
            if prep.status != 'FAILED' and latest and latest.preparation_id == prep.preparation_id:
                package = self.store._package(document.problem, document.statements[-1], len(document.packages)+1, actor, now(), preparation=prep)
            return self._append(document,digest,prep,self._event(document,prep,
                'preparation_failed' if prep.status == 'FAILED' else 'preparation_completed',actor,prep.failure_code),package)

    def suggest(self, identifier, request, actor):
        with self.store._locked():
            document,_ = self.store._owned(identifier,actor)
            self.store._expected(document,request)
            prep = self.store.latest_preparation(document)
            if not prep or prep.preparation_id != request.preparation_id or prep.status not in {'READY_FOR_REVIEW','REVIEW_REQUIRED'}:
                raise DynamicConflict('Prepare o enunciado atual antes de gerar uma rubrica.')
            prior = [r for r in document.rubrics if r.statement_version == len(document.statements)]
            base = prior[-1] if prior else None
        payload = dict(statement=document.statements[-1].model_dump(mode='json'),
            preparation=prep.proposal.model_dump(mode='json'), analysis=prep.analysis.model_dump(mode='json'),
            max_score=str(document.statements[-1].max_score), reason=request.reason,
            previous_rubric=base.model_dump(mode='json') if base else None)
        try:
            suggested, provenance = self.provider.generate('rubric', payload, SuggestedRubric)
            suggested = SuggestedRubric.model_validate(suggested.model_dump())
            if suggested.max_score != document.statements[-1].max_score or not suggested.criteria:
                raise ValueError('invalid generated total or empty rubric')
            review_payload = dict(**payload, proposed_rubric=suggested.model_dump(mode='json'))
            review, review_provenance = self.provider.generate('review_rubric', review_payload, SemanticReview)
            review = SemanticReview.model_validate(review.model_dump())
            warnings = rubric_warnings(suggested,prep,review)
            generation = RubricGeneration(preparation=PreparationReference(preparation_id=prep.preparation_id,
                preparation_version=prep.preparation_version,preparation_sha256=model_sha256(prep)),
                generation=provenance,semantic_review=review,review_provenance=review_provenance,
                warnings=warnings,previous_rubric_id=base.rubric_id if base else None,reason=request.reason)
        except Exception as exc:
            code = exc.code if isinstance(exc,ProviderFailure) else 'RUBRIC_INVALID_OUTPUT'
            with self.store._locked():
                current,digest = self.store._owned(identifier,actor)
                event = self._event(current,prep,'rubric_suggestion_failed',actor,code)
                if isinstance(exc,ProviderFailure) and exc.provenance:
                    event = event.model_copy(update=dict(generation_provenance=exc.provenance))
                self.store._append(current.model_copy(update=dict(revision=current.revision+1,events=(*current.events,event))),digest)
            raise ProviderFailure(code) from None
        return self.store.save_rubric(identifier, SaveRubric(expected_revision=request.expected_revision,
            statement_version=prep.statement_version,max_score=suggested.max_score,criteria=suggested.criteria),
            actor,base_id=base.rubric_id if base else None,generation=generation)


def rubric_warnings(suggested, preparation, review):
    warnings = list(suggested.warnings) + list(review.warnings)
    checks = {c.claim_id:c for c in preparation.analysis.verifier_plan}
    strategies = {s.strategy_id for s in preparation.proposal.alternative_strategies}
    seen = set()
    for c in suggested.criteria:
        identity = ' '.join(c.description.casefold().split())
        if identity in seen: raise ValueError('duplicate generated criterion')
        seen.add(identity)
        e = c.evidence
        if e is None:
            warnings.append(warning('NO_CRITERION_BINDING', 'Critério sem vínculo matemático explícito: '+c.criterion_id)); continue
        if not set(e.related_reference_claims) <= set(checks) or not set(e.accepted_alternative_strategies) <= strategies:
            raise ValueError('unknown rubric reference')
        if not e.related_reference_claims or any(checks[k].status != 'VERIFIED_WITHIN_SCOPE' for k in e.related_reference_claims):
            warnings.append(warning('UNVERIFIED_CRITERION', 'Critério depende de objetivo/claim não verificado: '+c.criterion_id))
        warnings.extend(warning('CRITERION_WARNING',c.criterion_id+': '+w) for w in e.warnings)
    labels = dict(overlap_detected='Possível sobreposição de pontuação.', vague_criteria='Há critérios excessivamente vagos.',
        impossible_dependency='Há dependência possivelmente impossível.', absent_information_required='Critério exige informação ausente.',
        unjustified_single_strategy='Possível exigência indevida de um único método.')
    for key, message in labels.items():
        if getattr(review,key): warnings.append(warning('SEMANTIC_'+key.upper(),message))
    return tuple(warnings)
