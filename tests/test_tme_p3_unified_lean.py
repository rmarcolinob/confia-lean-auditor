"""Real Lean with the final unified state/native-alias/award path; no API."""
import json
import pytest
from test_tme_semantic_formal_p3 import typed_claims,provider,award,result
from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import evaluate

@pytest.mark.parametrize('expression,status,score',[
    ('2/6=1/3','FORMAL_VERIFIED',2),
    ('2/6=1/2','FORMAL_REFUTED',0),
])
def test_real_lean_after_validated_retraction(expression,status,score,tmp_path):
    text='a) primeira_branca: 1/2\nCorrigindo minha afirmação anterior:\nprimeira_branca: '+expression
    r=evaluate('unified-lean-retraction','TME2026P3',text,extraction_provider=provider(typed_claims(text)),use_lean=True)
    (tmp_path/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    v=result(r,'a.first_white_probability')
    assert v['formal_status']==status and v['formal_attempted'] and r['score']==score
    assert v['checker_result']['compiled'] if score else v['checker_result']['refutation_verified']
    assert sum(d['resolved_discourse_state']=='SUPERSEDED' for d in r['discourse_decisions'])==2
    assert r['extractor']['api_calls']==0 and not r['fallback'] and not r['technical_uncertainty']
    assert award(r,'a.first_white_probability')['eligible']==bool(score)
    assert all(set(d['discourse_states'])=={'ACTIVE'} for d in r['veto_decisions'] if d['hard_veto_eligible'])
