const assert=require('node:assert/strict');
const eid = 'exam_'+'e'.repeat(32), aid='asmt_'+'a'.repeat(32);
const reply = data => ({ok:true,json:async()=>structuredClone(data)});
function backend({failUpload=false}={}) {
  const detail={submission:{submission_id:eid,page_count:4,original_documents:[{asset_id:'original_0001',media_type:'application/pdf'}],pages:Array.from({length:4},(_,i)=>({exam_page_id:'page_'+String(i).repeat(32),page_number:i+1,original_page_number:i+1,original_asset_id:'original_0001',preview_asset_id:`preview_000${i+1}`}))},
    participant:{external_code:'PROVA-1'},assessment:{assessment:{assessment_id:aid,title:'Avaliação configurada pelo backend'}},
    question_attempts:[1,2].map(i=>({case_id:'case_'+String(i).repeat(32),problem_id:'ITA2025F2Q'+i,question_order:i,exam_submission_id:eid,max_score:20,source_mode:'IMAGE_SCAN',external_candidate_ref:'PROVA-1'})),mapping:{version:1,bindings:[]}};
  let uploaded=false;const histories=new Map();
  const pagesFor=id=>detail.mapping.bindings.filter(b=>b.question_attempt_id===id).map(b=>detail.submission.pages.find(p=>p.exam_page_id===b.exam_page_id));
  return {detail,histories,mockFetch:async(url,options)=>{
    if(url==='/tme/assessments')return reply([detail.assessment]);
    if(url==='/tme/exam-submissions'&&options.method==='POST'){
      if(failUpload)return {ok:false,status:422,json:async()=>({detail:'PDF inválido.'})};
      uploaded=true;return reply(detail);
    }
    if(url==='/tme/exam-submissions')return reply(uploaded?[{submission_id:eid,participant_code:'PROVA-1',title:'Avaliação configurada pelo backend',page_count:4,question_count:2}]:[]);
    if(url===`/tme/exam-submissions/${eid}`)return reply(detail);
    if(url.endsWith('/page-mapping')){const body=JSON.parse(options.body);assert.equal(body.expected_version,detail.mapping.version);detail.mapping={version:detail.mapping.version+1,bindings:body.bindings};return reply(detail.mapping);}
    if(url.endsWith('/workspace')){
      const id=url.split('/')[3],history=histories.get(id)||null,latest=history?.revisions.at(-1);
      const versions=(history?.revisions||[]).map(r=>({version_id:`${r.transcription_id}:${r.revision_number}`,version_number:r.revision_number,origin:r.revision_number>1?'human':history.transcription.source==='capture'?'capture':'human',current:r===latest,text:r.segments.map(s=>s.text).join('\n'),created_at:'2026-11-10T12:00:00Z'}));
      return reply({question_attempt:detail.question_attempts.find(c=>c.case_id===id),pages:pagesFor(id),mapping_version:detail.mapping.version,
        history,versions,current_version:versions.at(-1)||null,state:history?'REVIEW':'PENDING',audits:[],audit_stale:false,
        reanalysis_required:(latest?.revision_number||0)>1,capture_candidate_available:!history,question_states:Object.fromEntries(detail.question_attempts.map(c=>[c.case_id,histories.has(c.case_id)?'REVIEW':'PENDING']))});
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
