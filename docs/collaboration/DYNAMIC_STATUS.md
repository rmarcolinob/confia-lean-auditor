# DYNAMIC — base de desenvolvimento, não versão concluída

Esta branch parte da RC1 integrada e da documentação de colaboração. Não modifica o snapshot SPECIALIZED nem acrescenta regras matemáticas. Seu propósito é permitir evolução revisada do DYNAMIC, separadamente da candidata congelada.

## O que existe

- Enunciados e rubricas versionados, rascunho, aprovação, contexto docente manual e preparação automática opcional: `dynamic/preparation.py::PreparationService`, modelos, stores e rotas.
- Atividades/listas/provas com várias questões, aprovação e ativação: `dynamic/assessment_service.py::{create,add,approve_many,activate}`.
- Grader com verificação exata de escopo limitado e evidências: `dynamic/grader.py::DynamicSolutionGrader`. O escopo exato reconhece famílias de equações lineares/quadráticas reais e padrões explícitos de critérios; não é um resolvedor geral de matemática.
- Avaliação semântica de pendências com solução integral e citações: `dynamic/semantic.py::{request_for,augment}`, política `dynamic-semantic.v1`, serviço semântico compartilhado. O código aplica os pesos da rubrica.
- Reviewer independente: `dynamic/reviewer.py::{blind_input,IndependentDynamicReviewer}` e `dynamic/semantic.py::review_phase`; recebe fonte/rubrica/evidências, sem a decisão do Grader como entrada.
- Reconciliação e regras por perfil: `dynamic/reconciliation.py::{SafeAutomationPolicy,reconcile_criteria}` e `dynamic/semantic.py::reconcile`. Concordância semântica é distinguida de verificação exata/formal. Pendências e falhas não viram zero.
- Integração com AuditService, QuestionAttempt, revisão de transcrição, workspace, decisão docente e histórico: `dynamic/product_adapter.py`, serviços de revisão/reconciliação e `submission_audits/`.

O fluxo atual aceita uma questão inédita com rubrica docente sem checker específico, microclaims ou formalização Lean preparados para aquela questão. Isso foi coberto por integração com providers simulados (`tests/test_dec10_integration.py`), incluindo questão fora do parser exato. Não demonstra acurácia de providers reais em questões arbitrárias. A inferência precisa estar disponível para decisões que dependem dela; sem provider, a pendência é explícita.

## Histórico preservado

`feat/dynamic-correction` em `5aa7344` é o marco histórico DY1–DY7. Os 109 arquivos locais R1 foram preservados em `74a6960`, com comparação byte a byte confirmada nesta organização. `77a5b7c` integra a política semântica e o piloto compartilhado. Os relatórios anteriores de DY7, feitos com fixtures maximalistas de Reviewer e antes dessa integração, não devem ser apresentados como medição atual do fallback.

Há ensaios reais antigos de providers sobre poucas soluções sintéticas (por exemplo, relatório DY4); não houve nova chamada paga nesta tarefa. Esses ensaios e benchmarks controlados não substituem gold independente nem validam generalidade.

## Próximos trabalhos e critérios de aceite

| Trabalho | Evidência necessária |
| --- | --- |
| Avaliação por domínio | Soluções independentes corretas, parciais, incorretas, alternativas e semanticamente ambíguas; gold separado do corretor |
| Rubricas propostas | Julgamento docente de clareza, cobertura, pesos e fidelidade ao enunciado; aprovação registrada antes da correção |
| Grader/Reviewer | Medir decisões por critério, citações válidas, divergências, crédito indevido, subcrédito e abstenções; manter cegamento do Reviewer |
| Revisão e retomada | Demonstrar falha técnica, reprocessamento explícito, invalidação de revisões antigas e confirmação humana sem perder histórico |
| Custo e latência | Medir tokens, custo e duração por etapa e critério; declarar modelo/configuração e amostra |
| Captura | Avaliar imagem → transcrição → revisão → correção separadamente; não atribuir falha de OCR ao raciocínio |
| Segurança | Manter autorização, isolamento institucional/por caso e gold inacessível ao processo corretor |

O Grader semântico chama o provider para critérios pendentes e o Reviewer semântico para os critérios de sua revisão, sequencialmente. Isso pode elevar custo e latência; não há benchmark representativo que autorize promessa de escala. Não alterar essa política sem um estudo específico e revisão.

Regressões existentes: `tests/test_dynamic_*.py`, `tests/test_dec10_integration.py` e testes JS de assessment/workspace. Nesta organização, o conjunto dirigido que inclui integração DYNAMIC, R1, diagnósticos e autorização passou com 152 testes Python; navegação/apresentação/caderno passaram com 45 testes JS. Não se declara toda a suíte DYNAMIC reexecutada. Estado: **piloto funcional em desenvolvimento, sem validação independente de eficácia**.
