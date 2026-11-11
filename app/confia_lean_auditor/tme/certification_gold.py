"""Independent, versioned human gold. Never updates correction artifacts."""
import csv
from datetime import datetime, timezone
from decimal import Decimal
import io
import json
import os
from typing import Optional, Literal
from pydantic import Field, model_validator
from fastapi import HTTPException

from confia_lean_auditor.assessments.store import assessment_store
from confia_lean_auditor.assessments.participants import participant_store
from confia_lean_auditor.assessments.models import AssessmentParticipant
from confia_lean_auditor.submissions.schemas import SubmissionModel
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.teacher_decisions.models import Points
from .exam_store import exam_store, ExamConflict, sealed, read_sealed


class GoldRubric(SubmissionModel):
    rubric_item_id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_.:-]+$')
    gold_points: Points
    max_points: Points

    @model_validator(mode='after')
    def bounds(self):
        if self.max_points <= 0 or self.gold_points > self.max_points: raise ValueError('invalid rubric score')
        return self


class GoldRow(SubmissionModel):
    assessment_id: str = Field(pattern=r'^asmt_[0-9a-f]{32}$')
    participant_code: str = Field(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9._:/-]+$')
    question_id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_.:-]+$')
    gold_score: Points
    max_score: Points
    rubric_gold: list[GoldRubric] = Field(default_factory=list, max_length=100)
    scorer_reference: Optional[str] = Field(default=None, min_length=1, max_length=80, pattern=r'^[A-Za-z0-9_.:-]+$')

    @model_validator(mode='after')
    def bounds(self):
        if self.max_score <= 0 or self.gold_score > self.max_score: raise ValueError('invalid gold score')
        if len({r.rubric_item_id for r in self.rubric_gold}) != len(self.rubric_gold): raise ValueError('duplicate rubric item')
        return self


class GoldImport(SubmissionModel):
    source_id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_.:-]+$')
    dataset_version: str = Field(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9_.:-]+$')
    expected_version: int = Field(ge=0)
    rows: list[GoldRow] = Field(min_length=1, max_length=10000)


class CertificationConfig(SubmissionModel):
    schema_version: Literal['certification-config.v1'] = 'certification-config.v1'
    assessment_id: str
    evaluation_mode: Literal['SHADOW_EVALUATION'] = 'SHADOW_EVALUATION'
    official_correction_affected: Literal[False] = False


def enabled():
    return os.environ.get('CONFIA_TME_CERTIFICATION_ENABLED', '0').lower() in {'1','true'}


def owned_assessment(aid, user):
    if not enabled(): raise HTTPException(404, 'Certificação não habilitada neste ambiente.')
    doc = assessment_store().get(aid)
    if doc.assessment.scope != 'TME' or doc.assessment.teacher_user_id != user.user_id:
        raise HTTPException(403, 'Avaliação fora do escopo do avaliador.')
    return doc


def folder(aid):
    # aid has already been validated by assessment_store.get; reject symlinks.
    root = exam_store().root / '.certification'
    target = root / aid
    if root.is_symlink() or target.is_symlink(): raise ExamConflict('invalid certification directory')
    return target


def history(aid):
    previous, rows = None, []
    for index, path in enumerate(sorted(folder(aid).glob('gold_*.json')), 1):
        try:
            data = read_sealed(path)
            if path.name != f'gold_{index:06d}.json' or data['version'] != index or data['previous_sha256'] != previous:
                raise ValueError('invalid gold chain')
            request = GoldImport.model_validate(data['request'])
            if any(r.assessment_id != aid for r in request.rows): raise ValueError('gold assessment mismatch')
            if canonical_sha256(data['request']) != data['request_sha256']: raise ValueError('invalid request digest')
            if canonical_sha256(data['records']) != data['records_sha256']: raise ValueError('invalid records digest')
        except (ValueError, KeyError, TypeError): raise ExamConflict('invalid gold history') from None
        previous = canonical_sha256(data); rows.append(data)
    if rows and read_sealed(folder(aid)/'config.json') != CertificationConfig(assessment_id=aid).model_dump(mode='json'):
        raise ExamConflict('invalid shadow configuration')
    return rows


def selected_gold(aid, version=None):
    versions = history(aid)
    if version is not None:
        match = next((v for v in versions if v['version']==version), None)
        if not match: raise FileNotFoundError()
        return match, versions
    return (versions[-1] if versions else None), versions


def csv_import(raw, source_id, dataset_version, expected_version):
    try:
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), strict=True)
        required = {'assessment_id','participant_code','question_id','gold_score','max_score'}
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or set(reader.fieldnames) != required:
            raise ValueError('CSV requires exactly assessment_id,participant_code,question_id,gold_score,max_score')
        rows = list(reader)
        if any(None in r or any(v is None for v in r.values()) for r in rows): raise ValueError('invalid CSV row')
        return GoldImport(source_id=source_id,dataset_version=dataset_version,expected_version=expected_version,rows=rows)
    except (UnicodeError, csv.Error): raise ValueError('invalid UTF-8 CSV') from None


def import_gold(aid, request, user):
    doc = owned_assessment(aid,user)
    with exam_store()._locked():
        versions = history(aid)
        content = request.model_dump(mode='json')
        digest = canonical_sha256(content)
        prior = next((v for v in versions if (v['source_id'],v['dataset_version']) == (request.source_id,request.dataset_version)), None)
        if prior:
            if prior['request_sha256'] != digest: raise ExamConflict('dataset version already used')
            return prior
        if request.expected_version != len(versions): raise ExamConflict('gold changed before import')
        participants = []
        ps = participant_store()
        with ps._locked():
            for p in ps.root.glob('part_*.json'):
                if p.is_symlink(): raise ExamConflict('invalid participant path')
                record = AssessmentParticipant.model_validate_json(p.read_bytes())
                if record.assessment_id == aid and record.participant_kind == 'EXTERNAL_PSEUDONYM': participants.append(record)
        records, seen = [], set()
        for row in request.rows:
            if row.assessment_id != aid: raise ValueError('row belongs to another assessment')
            matches = [p for p in participants if p.external_code == row.participant_code]
            if len(matches) != 1: raise ValueError('unknown or ambiguous participant code')
            items = [i for i in doc.items if row.question_id in (i.assessment_item_id,i.problem_id)]
            if len(items) != 1: raise ValueError('unknown or ambiguous question; use assessment_item_id')
            item = items[0]
            if Decimal(str(item.points)) != row.max_score: raise ValueError('incompatible maximum')
            key = (matches[0].participant_id,item.assessment_item_id)
            if key in seen: raise ValueError('duplicate participant/question')
            seen.add(key)
            # Rubric IDs/limits validated against a persisted audit, never a guessed rubric.
            if row.rubric_gold:
                from .certification import rubric_catalog
                catalog = rubric_catalog(aid,item.assessment_item_id,user)
                if not catalog: raise ValueError('rubric gold requires an observed rubric')
                for r in row.rubric_gold:
                    if r.rubric_item_id not in catalog or Decimal(str(catalog[r.rubric_item_id])) != r.max_points:
                        raise ValueError('unknown rubric item or incompatible maximum')
            records.append(dict(**row.model_dump(mode='json'), participant_id=key[0], assessment_item_id=key[1],
                problem_id=item.problem_id, gold_record_id='gold_'+canonical_sha256([aid,len(versions)+1,*key])[:32]))
        config = CertificationConfig(assessment_id=aid).model_dump(mode='json')
        target = folder(aid);target.mkdir(parents=True,exist_ok=True,mode=0o700)
        if not (target/'config.json').exists():
            SubmissionStore._write_atomic_new(target/'config.json',json.dumps(sealed(config)).encode())
        else:
            if read_sealed(target/'config.json') != config: raise ExamConflict('invalid shadow configuration')
        value = dict(schema_version='human-gold-dataset.v1',version=len(versions)+1,source_id=request.source_id,
            dataset_version=request.dataset_version,assessment_id=aid,evaluation_mode='SHADOW_EVALUATION',
            imported_at=datetime.now(timezone.utc).isoformat(),imported_by=user.user_id,
            previous_sha256=canonical_sha256(versions[-1]) if versions else None,
            request=content,request_sha256=digest,records=records,records_sha256=canonical_sha256(records))
        SubmissionStore._write_atomic_new(target/f'gold_{value["version"]:06d}.json',json.dumps(sealed(value),ensure_ascii=False,indent=2).encode())
        return value
