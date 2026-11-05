"""Experimental numeric view; the historical assessment is never mutated."""
import math


class ScoreClosurePolicy:
    version = 'c1-known-authorized-points.v1'

    def close(self, assessment, *, technical_uncertainty=False, review_recommended=False):
        score = float(assessment.known_points if assessment.score is None else assessment.score)
        if not math.isfinite(score) or not 0 <= score <= float(assessment.max_score):
            raise ValueError('invalid_numeric_score')
        technical = technical_uncertainty or any(i.technical_error_obligations for i in assessment.items)
        return dict(score=score, technical_uncertainty=bool(technical),
            review_recommended=bool(review_recommended or technical or assessment.needs_review),
            score_closure=dict(policy=self.version, applied=assessment.score is None,
                original_score=None if assessment.score is None else float(assessment.score),
                known_points=float(assessment.known_points), possible_points=float(assessment.possible_points)))
