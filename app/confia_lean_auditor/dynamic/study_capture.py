"""Small source adapter into the existing originals/transcription/OCR store."""
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import tempfile,os,shutil
from hashlib import sha256
from confia_lean_auditor.submissions.schemas import SubmissionRecord,SubmissionReceipt,ArtifactReference,CreateTranscriptionRequest
from confia_lean_auditor.tme.exam_capture import prepare
from .study_models import StudySourceSnapshot,StudyPage


def receive(store,study_id,problem_id,purpose,body,user):
    originals,rendered=prepare(SimpleNamespace(original_documents=body.original_documents,pages=[])) if body.original_documents else ([],[])
    snap=StudySourceSnapshot(snapshot_id='study:'+uuid4().hex,problem_id=problem_id,study_id=study_id,
        author_id=user.user_id,purpose=purpose,original_text=body.text,
        pages=[StudyPage(index=i,page_id='page_'+str(i+1),derived_width=p[3],derived_height=p[4],original_index=p[0],original_page=p[1]) for i,p in enumerate(rendered)])
    raw=snap.model_dump_json().encode()
    def ref(name,data,mime,**kw):return ArtifactReference(filename=name,media_type=mime,sha256=sha256(data).hexdigest(),size_bytes=len(data),**kw)
    original_refs=[ref(f'original_{i+1}.bin',data,body.original_documents[i].media_type) for i,data in enumerate(originals)]
    pages=[ref(f'page_{i+1}.png',p[2],'image/png',page_index=i,page_id=snap.pages[i].page_id) for i,p in enumerate(rendered)]
    record=SubmissionRecord(submission_id='sub_'+uuid4().hex,problem_id=problem_id,snapshot_id=snap.snapshot_id,
        source='self_study',capture_schema_version='self-study-source.v1',received_at=datetime.now(timezone.utc),
        snapshot=ref('snapshot.json',raw,'application/json'),page_images=pages,scan_originals=original_refs or None,
        submitted_by_user_id=user.user_id,tenant_id=user.tenant_id)
    receipt=SubmissionReceipt(**record.model_dump())
    with store._locked(exclusive=True):
        pending=Path(tempfile.mkdtemp(prefix='.pending-',dir=store.root))
        try:
            for name,data in [('snapshot.json',raw),('submission.json',record.model_dump_json().encode()),('receipt.json',receipt.model_dump_json().encode()),*[(r.filename,b) for r,b in zip(original_refs,originals)],*[(r.filename,p[2]) for r,p in zip(pages,rendered)]]:store._write(pending/name,data)
            store._sync_directory(pending);os.replace(pending,store.root/record.submission_id);store._sync_directory(store.root)
        finally:
            if pending.exists():shutil.rmtree(pending)
    if body.text:
        store.create_transcription(record.submission_id,CreateTranscriptionRequest(reviewer_reference=user.user_id,
            segments=[dict(segment_id='text:0',page_index=0,order=0,kind='text',text=body.text)]))
    return record.submission_id
