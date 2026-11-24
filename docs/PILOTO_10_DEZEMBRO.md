# Piloto integrado de 10/12/2026

Implementação em `codex/dec10-functional-integration`, derivada de
`feat/dynamic-correction` (`5aa7344`). O commit `74a6960` preserva todos os
109 arquivos locais do trabalho R1, incluindo experimentos e resultados.
Os worktrees originais não foram usados como destino das alterações.

## Iniciar localmente

Na raiz do worktree de integração, com as dependências Python instaladas:

```sh
python scripts/pilot_dec10.py --port 8010
```

Neste computador, o interpretador já disponível é
`/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`.
O launcher importa o código do próprio worktree, mesmo usando esse interpretador.
O armazenamento padrão é `runtime/pilot-dec10`, isolado dos outros ambientes.
Use `--data-dir CAMINHO` para outra base. O servidor é uma demonstração local,
sem autenticação, restrita a `127.0.0.1`; não é um comando de implantação pública.

- `/#teacher/home`: área do Professor, com SPECIALIZED, DYNAMIC, fila,
  resultados e os acessos institucionais existentes.
- `/tme?view=new`: seleção SPECIALIZED / DYNAMIC, com retorno à área do Professor.
- `/#student/home` e `/#management/home`: áreas preservadas do Aluno e da Gestão.
  A seleção de perfis é demonstrativa quando a autenticação está desativada;
  em sessão autenticada, o perfil continua definido pelo servidor.
- As atividades institucionais exigem sessão e vínculos de escola/turma.
  O piloto local apresenta essa limitação na interface, sem remover o 401.
- SPECIALIZED: selecionar avaliação preparada, receber a solução, revisar/aceitar
  a transcrição e executar a auditoria. TME² conserva a pauta e a escala de 20.
- DYNAMIC: criar atividade/prova, adicionar o enunciado, abrir “Revisar Q…”,
  fornecer e salvar critérios, aprovar a rubrica e voltar à avaliação para ativá-la.
  A rubrica docente recebe um registro local de contexto automaticamente;
  não exige uma solução de referência gerada, microclaims, checker ou arquivo Lean.
- Receber as soluções na avaliação ativa; aceitar a transcrição, executar a
  auditoria, solicitar revisão independente e reconciliar. Confirmar a sugestão
  na interface compartilhada antes do fechamento e da disponibilização do feedback.

## Providers e estados

O launcher não habilita inferência paga. Sem provider, os critérios que precisam
de avaliação semântica ficam pendentes com falha técnica registrada; o sistema
não inventa uma nota. Os testes usam providers simulados, nunca um modelo falso
injetado no servidor do piloto.

Após autorização explícita para chamadas reais, o provider semântico usa
`OPENAI_API_KEY` e `CONFIA_SEMANTIC_LLM_ENABLED=1`. O modelo padrão é
`gpt-6.1-sol`, esforço `medium`, como no experimento de referência; ajustes ficam
em `CONFIA_SEMANTIC_MODEL` e `CONFIA_SEMANTIC_REASONING_EFFORT`.
Cada chamada tem timeout de 60 segundos, sem retry automático, e limite de 4.000
tokens de saída. A disponibilidade do identificador do modelo deve ser conferida
na conta usada para o piloto. Não houve chamada paga nesta integração.

As sugestões automáticas de preparação/rubrica usam o provider DYNAMIC já
existente: exigem separadamente `CONFIA_DYNAMIC_LLM_ENABLED=1` e a chave,
com `CONFIA_DYNAMIC_MODEL` e `CONFIA_DYNAMIC_REASONING_EFFORT` opcionais.
O professor pode usar a entrada manual sem habilitar essa geração.

O fallback retorna apenas `met`, `not_met` ou `review`, justificativa e citações
literais. O código aplica os pontos da rubrica. O Grader mantém as decisões exatas
e usa fallback nas pendências. O Reviewer recebe enunciado, rubrica, solução e
evidência matemática, sem a decisão do Grader. A reconciliação preserva a
distinção entre concordância semântica, verificação exata e certificação formal.

`not_met` conclusivo pode produzir zero. Abstenção, divergência ou falha técnica
deixam o total pendente (`null`) e bloqueiam a confirmação dessa sugestão.
Uma sugestão semântica concordante ainda exige confirmação docente.
Requests, respostas, hashes, citações, versão da política e metadados do provider
ficam nos artefatos existentes de auditoria/revisão/reconciliação.

O custo semântico é limitado a uma chamada por critério elegível no SPECIALIZED;
no DYNAMIC há uma por critério pendente no Grader e uma por critério no Reviewer.
São chamadas sequenciais: a latência aumenta com o número de critérios. Repetir
a mesma execução persistida não chama o provider novamente. Uma nova revisão
explícita pode gerar novas chamadas. Não foi feito benchmark de custo/latência.

## Reversão

Parar o servidor e iniciar com a mesma base:

```sh
python scripts/pilot_dec10.py --port 8010 --legacy
```

Equivale a `CONFIA_SPECIALIZED_POLICY=legacy` e `CONFIA_DYNAMIC_POLICY=legacy`.
As novas configurações usam a política anterior. Auditorias, revisões e avaliações
DYNAMIC já publicadas mantêm a política fixada nos respectivos registros;
não são reinterpretadas ou apagadas. Para corrigir com outra política, criar uma
nova configuração/tentativa/publicação, preservando as anteriores.

## Verificação local

```sh
PYTHONPATH=app python -m pytest tests/test_dec10_integration.py tests/test_dec10_specialized.py -q
node --test tests/js/test_*.cjs
```

Os testes funcionais cobrem ITA sem dupla adjudicação, TME² com PautaEngine,
questão inédita fora do parser de equações, rubrica docente, Grader, Reviewer
cego, reconciliação, submissão/transcrição, persistência, confirmação/fechamento,
abstenção, falha técnica, zero e leitura do histórico após reversão.
São testes de integração e contratos, não validação da acurácia matemática GPT.

Lean requer o toolchain de `lean-toolchain` e o cache `.lake` correspondente.
O cache local foi copiado com clone de arquivos para este worktree, sem substituir
checkers ou alterar o ambiente original. Não se deve interpretar erro de instalação
Lean como refutação matemática.

A validação matemática extensa com gold humano e a avaliação dos providers reais
continuam pendentes. A aprovação operacional do piloto deve considerar essas
limitações, além dos resultados dos testes locais.
