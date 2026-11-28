# Correção direta em página única — 10/12/2026

Atualização de 28/11/2026 na branch local `codex/teacher-direct-dec10`, sobre `58253fa4b41f039a2ab6949eec7b5fbf55ecacc3`, que descende do HEAD do PR #11 `f16314e440ce43587843105cae6ee64f943c8de6`. Esta página substitui o roteiro inicial de entrada com transcrição manual. A implementação anterior e seu relatório permanecem no histórico Git.

## Interface entregue

A página inicial do professor, cores, tipografia e arquivos de estilos permanecem iguais. Nenhuma mudança em main, PR #11, motores, backend, pautas, contratos científicos, módulos de Aluno/Gestão ou regras de pontuação.

DYNAMIC apresenta em uma página: título opcional, enunciado, pontuação total, rubrica, solução e resultado. Cada critério tem somente três campos editáveis — título, descrição e pontos — e pode ser adicionado/removido. A soma é validada em centésimos; valores inconsistentes impedem a aprovação. O botão principal é **Corrigir solução**. O resultado, evidências e pendências aparecem abaixo, sem encaminhamento obrigatório a outra tela.

A aprovação continua explícita e persistida pelos serviços existentes. Quando o servidor apresenta novos avisos, estes precisam ser lidos e reconhecidos na mesma página antes da aprovação. Editar enunciado, total ou critério invalida a aprovação local e exige uma nova versão aprovada. Rubricas existentes conservam crédito parcial, dependências, evidências, notas, orientação docente e proveniência. Seus campos científicos não são descartados pela edição simplificada. Remover um pré-requisito ainda referenciado é recusado; reduzir pontos abaixo de um nível parcial também bloqueia aprovação.

A sugestão por IA utiliza preparação e sugestão existentes, quando configuradas. Nesta validação a opção ficou indisponível, com todos os providers desligados. Nenhuma chamada paga foi feita.

SPECIALIZED conserva a seleção do catálogo e usa a mesma entrada simples: escolher solução digital, confirmar seu conteúdo e corrigir. O relatório aparece na própria página. Os serviços de correção, versões, aceites e relatórios são os mesmos do PR #11 e da adaptação anterior. O editor completo e as entradas antigas continuam acessíveis pelas rotas existentes; não são etapas obrigatórias do percurso direto.

## Imagens e integração do Luis

A interface oferece **Tirar foto** (seletor nativo com `capture=environment`, conforme o dispositivo) e **Fazer upload** de PDF/JPG/PNG/WebP. Enquanto a integração automática não está conectada, o arquivo fica somente em visualização local. A interface informa isso, não o envia ao corretor, não gera transcrição e mantém **Corrigir solução** desabilitado. Não solicita transcrição manual de manuscritos.

A opção separada **Solução já digital** permite colar uma solução que já existe em texto e testar os motores. Ela não interpreta nem envia a imagem selecionada. Trocar de texto digital para imagem invalida a confirmação e impede que texto antigo seja confundido com reconhecimento da nova imagem.

Foi preparado `ConfIATeacherDirect.create(...).loadAutomaticCase(caseId)` para consumir uma leitura automática **já persistida no servidor**. Ele usa os contratos atuais de caso, submissão, transcrição, revisão, aceite e auditoria; não recebe texto de OCR arbitrário do cliente nem regrava reconhecimento como transcrição manual. Verifica problema/motor, origem automática, revisão atual e trechos não resolvidos, mostra originais e leitura e solicita conferência, sem digitação obrigatória. A auditoria usa os identificadores e a proveniência originais. Se a leitura mudar, a confirmação anterior não autoriza a versão nova.

Esse ponto de consumo não é um OCR funcional nem a integração completa de upload/captura do Luis. Falta conectar a produção da leitura automática ao caso persistido. Casos de avaliação inteira mantêm seu caminho próprio de associação/conferência; não são reinterpretados como casos diretos.

## Validação desta alteração

- **644 testes JavaScript aprovados**: página única; soma; aprovação explícita; nova versão após edição; preservação de campos científicos; erro de armazenamento sem perder campos; bloqueio de imagens; integração futura por leitura persistida; rejeição de fonte manual/ambígua/de outro problema; revisão alterada; identidade de execução estável após perda de resposta; regressões anteriores.
- **27 testes Python aprovados**: `tests/test_teacher_direct.py` e `tests/test_dynamic_dy1.py`, com autenticação real, isolamento, versões/rubricas e os percursos dos dois motores. Providers e credenciais externas ausentes.
- **Lean build aprovado: 8.038 jobs**, antes dos testes formais.
- **Smoke de eventos JavaScript de produção contra HTTP real**, em `127.0.0.1:8888`, com conta sintética, DOM de teste e renderizador capturando os resultados reais. Não é um teste visual. DYNAMIC: problema novo, rubrica manual aprovada após avisos, solução digital, confirmação, Grader, Reviewer, Reconciliation; nota e nota reconciliada nulas, revisão necessária. SPECIALIZED: TME² P1 completo, **20/20**, duas checagens Lean efetivamente compiladas (`731-137=594`, `3*10=30`). Nenhuma avaliação publicada, divulgação ou decisão humana automática.
- `git diff --check` aprovado. Arquivos da home, estilos e backend sem alterações nesta entrega.

Testes de DOM/transporte usam respostas sintéticas identificadas nos arquivos e não demonstram inferência matemática real. O smoke HTTP e os testes integrados usam motores reais com providers desligados. Uma nota DYNAMIC indeterminada não foi substituída por parecer simulado; as verificações Lean de duas expressões não equivalem à formalização integral da solução.

A suíte completa Python do PR #11 não foi repetida; não houve alteração dos motores. Os resultados da validação anterior estão no histórico do relatório.

Logs locais ignorados pelo Git: `artifacts/direct-simple/javascript.log`, `python.log`, `lean-build.log`, `real-page-smoke.log` e `real-page-results.json`.

A automação visual voltou a falhar: host do navegador indisponível e timeout no acesso nativo ao Chrome. **Não há aprovação de layout, teclado ou console de navegador nesta execução.** Os estilos existentes foram preservados por diff, não por uma inspeção visual automatizada bem-sucedida.

## Roteiro curto

Iniciar no worktree `/private/tmp/confia-teacher-direct-dec10`:

```sh
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/run_teacher_direct_demo.py
```

Abra `http://127.0.0.1:8888/` e use o login/senha local informados pelo script. Os providers ficam desligados e a autenticação é real. Se o servidor já estiver ativo, recarregue a página para carregar os scripts atualizados.

1. **DYNAMIC:** preencha enunciado e total; adicione critérios simples cuja soma coincida com o total. Clique **Aprovar rubrica**, confira os avisos e confirme a aprovação na própria página. Não é necessário cadastrar atividade, turma ou aluno.
2. Escolha **Solução já digital**, cole o texto, confirme seu conteúdo e clique **Corrigir solução**. Mostre resultado, evidências e pendências abaixo. Com provider desligado, explique a abstenção semântica; não anuncie nota automática completa.
3. Escolha **Foto ou upload** e selecione uma imagem sintética. Mostre o original e o aviso de leitura indisponível: nenhuma transcrição ou nota é produzida, e não se pede digitação do manuscrito.
4. **SPECIALIZED:** selecione TME² Problema 1 e cole [a solução digital sintética](teacher-direct-tme-p1.txt), preservando os marcadores de item. Confirme e corrija. Mostre 20/20, evidências e as duas verificações Lean executadas.
5. Abra o histórico, se necessário; confirme que não houve divulgação. Verifique no navegador real foco por teclado, retorno à home, carregamento do original e console.

O percurso digital está validado. A demonstração com manuscritos depende da integração automática do Luis; julgamento semântico real por LLM continua exigindo autorização específica de modelo, custo e número de chamadas.
