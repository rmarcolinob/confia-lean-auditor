"""Independent synthetic textual probes. No mocked mathematical providers or OCR.
Run via runtime/audit-pre10dez/run_offline.py to isolate environment and stores.
Uses only the public HTTP services and the existing synthetic account fixture.
"""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'tests')]
import pytest
from test_core_auth import auth_case
from test_dynamic_dy3 import attempt

CASES=[
 ('linear','Resolva nos reais: 3x-9=0.',[
  ('correct','3x=9; x=3'),('wrong_sign','x=-3'),('answer_only','x=3'),('alternative','Dividir ambos os membros por três dá x-3=0, portanto x=3.'),('hypothesis','Se x=3, então a equação vale.'),('quoted','O colega escreveu "x=3", mas não avaliei sua solução.')]),
 ('quadratic','Resolva nos reais: x²-9x+20=0.',[
  ('correct','(x-4)(x-5)=0; S={4,5}'),('partial','x=4'),('wrong','S={-4,-5}'),('retracted','Descarto: x=8; S={4,5}'),('false_step','x²-9x+20=0; (x-4)(x-6)=0; S={4,5}'),('answer_only','S={4,5}')]),
 ('fractions','Calcule dois quintos de 35 e explique o raciocínio.',[('correct','35/5=7; 2*7=14. Dividi em cinco partes iguais e tomei duas.'),('wrong','35/5=8; 2*8=16.'),('partial','35/5=7'),('answer_only','14')]),
 ('geometry','Um retângulo mede 7 cm por 4 cm. Calcule seu perímetro e justifique.',[('correct','São dois lados de 7 e dois de 4: 7+4+7+4=22 cm.'),('wrong','7*4=28 cm.'),('partial','7+4=11'),('alternative','P=2*(7+4)=22 cm, pois lados opostos são iguais.')]),
 ('probability','Uma urna tem 3 bolas azuis e 5 vermelhas. Qual a probabilidade de retirar uma bola azul?', [('correct','Há 8 resultados equiprováveis e 3 favoráveis: 3/8.'),('wrong','3/5'),('partial','Há 8 bolas no total.'),('alternative','A chance de vermelha é 5/8; o complemento é 1-5/8=3/8.')]),
 ('functions','Para f(x)=2x+3, determine f(4) e explique.',[('correct','Substituo x por 4: f(4)=2*4+3=11.'),('wrong','f(4)=2*(4+3)=14.'),('partial','f(4)=2*4+3'),('answer_only','11')]),
]

def checked(response,code):
 assert response.status_code==code,(response.status_code,response.text)
 return response.json()

def main():
 mp=pytest.MonkeyPatch();out=ROOT/'runtime/audit-pre10dez/textual';out.mkdir(parents=True,exist_ok=True)
 for key in ('AUTH','INSTITUTIONAL','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TME_EXAMS','TME_CASES','SUBMISSIONS','SUBMISSION_AUDITS','DYNAMIC','TEACHER_DECISIONS','SELF_STUDY'):mp.setenv('CONFIA_'+key+'_DIR',str(out/key.lower()))
 mp.setenv('CONFIA_DYNAMIC_POLICY','dynamic-semantic.v1');mp.setenv('CONFIA_SPECIALIZED_POLICY','semantic-b-minimal.v1')
 auth=auth_case.__wrapped__(out,mp);client=auth[2]('teacher.a');results=[]
 for topic,statement,variants in CASES:
  d=checked(client.post('/dynamic/problems',json=dict(title='Auditoria sintética '+topic,statement=statement,max_score='10',correction_mode='DYNAMIC')),201);pid=d['problem']['problem_id']
  criteria=[dict(criterion_id='method',title='Desenvolvimento',description='Justificar a resolução por transformações equivalentes.' if topic in ('linear','quadratic') else 'Justificar matematicamente o procedimento e as hipóteses.',max_points='6',order=1),dict(criterion_id='answer',title='Resultado',description='Obter todas as raízes reais. Crédito parcial proporcional às raízes corretas.' if topic in ('linear','quadratic') else 'Apresentar o resultado correto com a unidade ou representação adequada.',max_points='4',order=2)]
  d=checked(client.post(f'/dynamic/problems/{pid}/rubrics',json=dict(expected_revision=d['revision'],statement_version=1,max_score='10',criteria=criteria)),201)
  d=checked(client.post(f"/dynamic/problems/{pid}/rubrics/{d['rubrics'][-1]['rubric_id']}/approve",json=dict(expected_revision=d['revision'],acknowledge_warnings=True)),200)
  for label,text in variants:
   case,base,body=attempt(client,d,text);run=checked(client.post(base+'/audits',json=body),200)
   prefix=f"/dynamic/attempts/{case['case_id']}";checked(client.post(prefix+'/policy',json={'policy_profile':'SCHOOL_EXAM'}),201)
   review=checked(client.post(prefix+f"/audits/{run['audit_run_id']}/independent-reviews",json={'execution_key':'audit-offline'}),201)['review']
   rec=checked(client.post(prefix+f"/audits/{run['audit_run_id']}/reconciliations",json={'independent_review_id':review['review_id']}),201)['reconciliation']
   result=run['result'];row=dict(topic=topic,variant=label,statement=statement,solution=text,rubric=criteria,status=run['status'],score=result['score'],reconciled_score=rec['reconciled_suggested_score'],review_required=rec['review_required'],technical_uncertainty=rec['technical_uncertainty'],decisions=result['decisions'],claims=result['analysis']['claims'],provenance=result['analysis']['provenance'],reviewer_phase_a_input=review['phase_a_input'],reconciliation_criteria=rec['criteria'])
   results.append(row);print(topic,label,'grader=',row['score'],'rec=',row['reconciled_score'],flush=True)
 (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 assert os.getenv('OPENAI_API_KEY') is None
 mp.undo()
if __name__=='__main__':main()
