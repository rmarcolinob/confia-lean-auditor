"""Short feedback projection from confirmed human scores; no generated solutions."""
def question_feedback(audit,decision,policy):
    if policy != 'AFTER_CONFIRMATION' or not decision:
        return dict(status='WITHHELD',criteria=[])
    return dict(status='AVAILABLE_AFTER_CONFIRMATION',human_decision_id=decision['human_decision_id'],
        final_points=decision['final_points'],criteria=[dict(criterion_id=i['rubric_item_id'],
            criterion=i['label'],recognized='Evidência reconhecida' if i['suggested_points'] else 'Evidência insuficiente ou não reconhecida',
            review_required=i['review_required'],suggestion='Confira a justificativa deste critério com o professor.' if i['review_required'] else 'Explique os passos utilizados e confira o resultado.') for i in audit['rubric_items']])
