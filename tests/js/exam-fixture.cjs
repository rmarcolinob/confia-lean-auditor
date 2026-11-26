const assert=require('node:assert/strict');
const eid = 'exam_'+'e'.repeat(32), aid='asmt_'+'a'.repeat(32);
const reply = data => ({ok:true,json:async()=>structuredClone(data)});
function backend({failUpload=false,auditResponder=null,decisionResponder=null,finalizationResponder=null}={}) {
  const detail={submission:{submission_id:eid,page_count:4,original_documents:[{asset_id:'original_0001',media_type:'application/pdf'}],pages:Array.from({length:4},(_,i)=>({exam_page_id:'page_'+String(i).repeat(32),page_number:i+1,original_page_number:i+1,original_asset_id:'original_0001',preview_asset_id:`preview_000${i+1}`}))},
    participant:{external_code:'PROVA-1'},assessment:{assessment:{assessment_id:aid,title:'Avaliação configurada pelo backend'}},
    question_attempts:[1,2].map(i=>({case_id:'case_'+String(i).repeat(32),problem_id:'ITA2025F2Q'+i,question_order:i,exam_submission_id:eid,max_score:20,source_mode:'IMAGE_SCAN',external_candidate_ref:'PROVA-1'})),mapping:{version:1,bindings:[]}};
  let uploaded=false;const histories=new Map(),audits=new Map(),decisions=new Map(),reopened=new Set();
  const pagesFor=id=>detail.mapping.bindings.filter(b=>b.question_attempt_id===id).map(b=>detail.submission.pages.find(p=>p.exam_page_id===b.exam_page_id));
  const currentDecision=id=>{const d=(decisions.get(id)||[])[0],r=(audits.get(id)||[])[0],v=histories.get(id)?.revisions.at(-1);return d&&!reopened.has(d.human_decision_id)&&r?.audit_run_id===d.audit_run_id&&r.revision_number===v?.revision_number?d:null;};
  let closure=null;const closures=[];
  const correction=()=>{
    const questions=detail.question_attempts.map(c=>{const d=currentDecision(c.case_id),v=histories.get(c.case_id)?.revisions.at(-1),r=(audits.get(c.case_id)||[]).find(r=>r.revision_number===v?.revision_number);
      const score=r?.status==='COMPLETED'?r.suggested_score:null;
      return {question_attempt_id:c.case_id,question_order:c.question_order,problem_id:c.problem_id,max_score:20,
        audit_run_id:r?.audit_run_id,human_decision_id:d?.human_decision_id,suggested_score:score??null,final_score:d?.final_points??null,adjustment:d?.adjustment_delta??null,
        review_required:r?.review_required||false,status:d?'CONFIRMED':'PENDING',blocker:d?null:'Questão ainda não confirmada.'};});
    const ready=questions.every(q=>q.status==='CONFIRMED'),scored=questions.filter(q=>q.suggested_score!=null),confirmed=questions.filter(q=>q.final_score!=null);
    const suggested=scored.reduce((s,q)=>s+q.suggested_score,0),final=confirmed.reduce((s,q)=>s+q.final_score,0);
    return {submission_id:eid,participant_code:'PROVA-1',assessment_title:detail.assessment.assessment.title,
      status:closure?'FINALIZED':closures.length?'REOPENED':ready?'READY_TO_FINALIZE':'IN_PROGRESS',ready_to_finalize:ready&&!closure,
      questions,question_count:questions.length,confirmed_question_count:confirmed.length,pending_question_count:questions.length-confirmed.length,
      review_question_count:questions.filter(q=>q.review_required).length,unconfirmed_review_question_count:0,adjusted_question_count:confirmed.filter(q=>q.adjustment).length,
      max_total:questions.length*20,suggested_total:scored.length?suggested:null,suggested_total_complete:scored.length===questions.length,
      final_total:confirmed.length?final:null,final_total_complete:ready,total_adjustment:ready?final-suggested:null,
      blockers:questions.filter(q=>q.blocker).map(q=>({...q,reason:q.blocker})),current_final_correction:closure,final_corrections:[...closures].reverse(),
      snapshot_sha256:JSON.stringify(questions.map(q=>[q.audit_run_id,q.human_decision_id]))};
  };
  return {detail,histories,audits,decisions,correction,mockFetch:async(url,options)=>{
    if(url===`/tme/exam-submissions/${eid}/correction`)return reply(correction());
    if(url===`/tme/exam-submissions/${eid}/correction/finalize`){
      const body=JSON.parse(options.body),intercepted=finalizationResponder?await finalizationResponder(body):null;
      if(intercepted?.status)return {ok:false,status:intercepted.status,json:async()=>({})};
      const data=correction();if(!data.ready_to_finalize||body.expected_snapshot_sha256!==data.snapshot_sha256)return {ok:false,status:409,json:async()=>({})};
      closure={...data,final_correction_id:'final_'+body.execution_key,version:closures.length+1,finalized_by:'demo-evaluator',finalized_at:'2026-11-11T04:00:00Z',suggested_total_snapshot:data.suggested_total};closures.push(closure);uploaded=true;detail.correction_status='FINALIZED';return reply(closure);
    }
    if(url===`/tme/exam-submissions/${eid}/correction/reopen`){closure=null;detail.correction_status='REOPENED';return reply({});}
    if(url==='/tme/assessments')return reply([detail.assessment]);
    if(url==='/tme/exam-submissions'&&options.method==='POST'){
      if(failUpload)return {ok:false,status:422,json:async()=>({detail:'PDF inválido.'})};
      uploaded=true;return reply(detail);
    }
    if(url==='/tme/exam-submissions')return reply(uploaded?[{submission_id:eid,participant_code:'PROVA-1',title:'Avaliação configurada pelo backend',page_count:4,question_count:2,status:closure?'FINALIZED':'IN_PROGRESS',final_total:closure?.final_total,adjusted_question_count:closure?.adjusted_question_count,finalized_at:closure?.finalized_at}]:[]);
    if(url===`/tme/exam-submissions/${eid}`)return reply(detail);
    if(url.endsWith('/page-mapping')){const body=JSON.parse(options.body);assert.equal(body.expected_version,detail.mapping.version);detail.mapping={version:detail.mapping.version+1,bindings:body.bindings};return reply(detail.mapping);}
    if(url.endsWith('/workspace')){
      const id=url.split('/')[3],history=histories.get(id)||null,latest=history?.revisions.at(-1);
      const versions=(history?.revisions||[]).map(r=>({version_id:`${r.transcription_id}:${r.revision_number}`,version_number:r.revision_number,origin:r.revision_number>1?'human':history.transcription.source==='capture'?'capture':'human',current:r===latest,text:r.segments.map(s=>s.text).join('\n'),created_at:'2026-11-10T12:00:00Z'}));
      const runs=(audits.get(id)||[]).map(r=>({...r,stale:r.revision_number!==latest?.revision_number}));
      const current=runs.find(r=>!r.stale), state=currentDecision(id)?'CONFIRMED':!history?'PENDING':current&&current.status==='COMPLETED'&&!current.review_required?'READY':'REVIEW';
      const currents=detail.question_attempts.map(c=>(audits.get(c.case_id)||[]).find(r=>r.revision_number===histories.get(c.case_id)?.revisions.at(-1).revision_number));
      const scored=currents.filter(r=>r?.status==='COMPLETED'&&r.suggested_score!=null);
      const partial_suggestion={suggested_score:scored.reduce((s,r)=>s+r.suggested_score,0),max_score:40,analyzed_questions:scored.length,total_questions:2,complete:scored.length===2,awaiting_reanalysis:currents.filter((r,i)=>(!r||r.status==='FAILED')&&(audits.get(detail.question_attempts[i].case_id)||[]).length).length};
      const confirmed=detail.question_attempts.map(c=>currentDecision(c.case_id)).filter(Boolean);
      const human_decisions=(decisions.get(id)||[]).map(d=>({...d,current:d===currentDecision(id)}));
      return reply({exam_finalized:!!closure,current_human_decision:currentDecision(id),human_decisions,last_human_decision_id:human_decisions[0]?.human_decision_id||null,
        question_decisions:Object.fromEntries(detail.question_attempts.map(c=>[c.case_id,currentDecision(c.case_id)])),
        confirmed_total:{final_score:confirmed.reduce((s,d)=>s+Number(d.final_points),0),max_score:confirmed.length*20,confirmed_questions:confirmed.length,total_questions:2,remaining_questions:2-confirmed.length},question_attempt:detail.question_attempts.find(c=>c.case_id===id),pages:pagesFor(id),mapping_version:detail.mapping.version,
        history,versions,partial_suggestion,previous_audit:runs.find(r=>r.stale)||null,audit_comparison:current?.comparison||null,current_version:versions.at(-1)||null,state,audits:runs,current_audit:current||null,audit_stale:runs.some(r=>r.stale)&&!current,
        reanalysis_required:(!current||current.status==='FAILED')&&(latest?.revision_number||0)>1,capture_candidate_available:!history,question_states:Object.fromEntries(detail.question_attempts.map(c=>[c.case_id,currentDecision(c.case_id)?'CONFIRMED':!histories.has(c.case_id)?'PENDING':(audits.get(c.case_id)||[]).some(r=>r.revision_number===histories.get(c.case_id).revisions.at(-1).revision_number&&!r.review_required)?'READY':'REVIEW']))});
    }
    if(url.startsWith('/tme/cases/')&&url.endsWith('/decision')&&options.method==='POST'){
      const id=url.split('/')[3],body=JSON.parse(options.body);
      const intercepted=decisionResponder?await decisionResponder(body,id):null;
      if(intercepted?.status)return {ok:false,status:intercepted.status,json:async()=>({})};
      const run=(audits.get(id)||[])[0],last=(decisions.get(id)||[])[0];
      if(currentDecision(id)||run?.audit_run_id!==body.audit_run_id||last?.human_decision_id!==(body.expected_last_decision_id||undefined))return {ok:false,status:409,json:async()=>({})};
      const final=body.decision_type==='ACCEPT_SUGGESTION'?run.suggested_score:Number(body.final_points);
      const decision={...body,human_decision_id:'hdec_'+body.execution_key,final_points:final,max_points:20,suggested_points:run.suggested_score,adjustment_delta:final-run.suggested_score,
        decided_by_user_id:'demo-evaluator',decided_at:'2026-11-11T03:00:00Z',review_required_snapshot:run.review_required};
      decisions.set(id,[decision,...(decisions.get(id)||[])]);return reply(decision);
    }
    if(url.endsWith('/reopen')){const body=JSON.parse(options.body);reopened.add(body.human_decision_id);return reply({});}
    if(url.startsWith('/tme/cases/')&&url.endsWith('/accept')){
      const id=url.split('/')[3],body=JSON.parse(options.body),acceptance={revision_number:body.revision_number,acceptance_id:'acc_'+id.slice(5)};
      histories.get(id).acceptances.push(acceptance);return reply({acceptance});
    }
    if(url.startsWith('/tme/cases/')&&url.endsWith('/audits')&&options.method==='POST'){
      const id=url.split('/')[3],body=JSON.parse(options.body);
      assert.ok(auditResponder,'test must explicitly provide an audit result');
      const result=await auditResponder(body,id);
      if(result?.httpError)return {ok:false,status:503,json:async()=>({})};
      const previous=(audits.get(id)||[]).find(r=>r.revision_number!==body.revision_number);
      if(previous)result.comparison={previous_audit_run_id:previous.audit_run_id,previous_suggested_score:previous.suggested_score,previous_max_score:previous.max_score,previous_transcription_version_id:previous.transcription_version_id,current_transcription_version_id:result.transcription_version_id,current_suggested_score:result.suggested_score,score_changed:previous.suggested_score!==result.suggested_score};
      audits.set(id,[result,...(audits.get(id)||[]).filter(r=>r.audit_run_id!==result.audit_run_id)]);return reply(result);
    }
    if(url.startsWith('/tme/cases/')&&url.endsWith('/transcriptions')&&options.method==='POST'){
      const id=url.split('/')[3],body=JSON.parse(options.body);
      if(histories.has(id))return {ok:false,status:409,json:async()=>({})};
      const transcription={transcription_id:'tr_'+id.slice(5),source:body.origin==='capture'?'capture':'manual',created_at:'2026-11-10T12:00:00Z'};
      const revision={...transcription,revision_number:1,segments:body.segments||[{segment_id:'capture:0',page_index:0,order:0,kind:'text',text:'x = 1'}]};
      histories.set(id,{transcription,revisions:[revision],acceptances:[]});return reply(revision);
    }
    if(url.startsWith('/tme/cases/')&&url.endsWith('/revisions')){
      const history=histories.get(url.split('/')[3]),body=JSON.parse(options.body);
      if(body.based_on_revision_number!==history.revisions.at(-1).revision_number)return {ok:false,status:409,json:async()=>({})};
      const revision={...history.transcription,revision_number:body.based_on_revision_number+1,segments:body.segments};history.revisions.push(revision);return reply(revision);
    }
    if(url.startsWith('/tme/question-attempts/')){const id=url.split('/').pop();return reply({question_attempt:detail.question_attempts.find(c=>c.case_id===id),pages:detail.mapping.bindings.filter(b=>b.question_attempt_id===id).map(b=>detail.submission.pages.find(p=>p.exam_page_id===b.exam_page_id))});}
  }};
}
module.exports={backend,eid,aid,reply};
