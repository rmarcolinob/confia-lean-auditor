/* UI orchestration only. Existing services own evidence, policy and scoring. */
(function(root){
  'use strict';
  async function complete({caseId,run,api,post}){
    if(run.engine_mode!=='DYNAMIC'||run.status!=='COMPLETED'||run.stale)return null;
    const base=`/dynamic/attempts/${encodeURIComponent(caseId)}/audits/${encodeURIComponent(run.audit_run_id)}`;
    const reconciliations=await api(base+'/reconciliations');
    const current=reconciliations.find(row=>!row.stale);
    if(current)return current;
    const reviews=await api(base+'/independent-reviews');
    let review=reviews.find(row=>!row.stale);
    // Stable within this audit: a lost response can be resumed without a second review.
    if(!review)review=await post(base+'/independent-reviews',{execution_key:'teacher-simplified'});
    if(review.stale||!review.review?.review_id)throw new Error('A revisão não pôde ser concluída. Recarregue a questão; nenhuma nota final foi confirmada.');
    return post(base+'/reconciliations',{independent_review_id:review.review.review_id});
  }
  root.ConfIADynamicCorrection={complete};
})(window);
