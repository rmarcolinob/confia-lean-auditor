# ConfIA — Confiabilidade e Explicabilidade

Plataforma experimental de correção matemática, resolução assistida e acompanhamento pedagógico. Backend Python/FastAPI, frontend HTML/CSS/JavaScript e verificações formais locais com Lean.

| Frente | Situação em 26/11/2026 | Referência |
| --- | --- | --- |
| SPECIALIZED | RC1 experimental congelada; avaliação independente com gold humano pendente | Tag `SPECIALIZED-TME2-RC1` |
| DYNAMIC | Professor, atividade institucional do aluno e estudo autônomo integrados; feedback público restrito da I6+6B; validação independente pendente | `main`, após revisão do PR de consolidação |
| Interface | Professor baseado no TME²; entrada, Aluno e Gestão harmonizados | `main`, após revisão do PR de consolidação |
| Colaboração | Instalação, limites, inventário e orientações para revisão | Documentação neste repositório |

A `main` é a referência integrada e testada da plataforma. Novos trabalhos partem dela e retornam por pull requests revisados. Esta consolidação só atualiza a `main` após aprovação humana do PR; até lá, a versão completa está em `codex/main-consolidation-dec10`. Integração técnica não significa aprovação para produção. O vídeo institucional é um projeto separado em `codex/interface-video`, com exemplos ilustrativos.

## Começar

Rian e Luis devem usar a `main` após o merge do PR de consolidação. Para avaliar o PR antes disso, execute `git switch --track origin/codex/main-consolidation-dec10` depois do clone.

```sh
git clone https://github.com/rmarcolinob/confia-lean-auditor.git
cd confia-lean-auditor
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e . -c docs/audits/assets/dynamic-rc1/python-constraints.txt
```

Para executar **os três contextos completos**, continue com o [ambiente autenticado de desenvolvimento](docs/collaboration/README.md#dynamic-com-sessão-autenticada), incluindo contas e vínculos locais. Para abrir somente a demonstração visual sem sessão:

```sh
env -u OPENAI_API_KEY CONFIA_SEMANTIC_LLM_ENABLED=0 CONFIA_DYNAMIC_LLM_ENABLED=0 \
  .venv/bin/python scripts/pilot_dec10.py --port 8010
```

Instalar dependências pode acessar a rede. O launcher inicia **demonstração local em 127.0.0.1**, com armazenamento próprio e sem habilitar providers pagos. Não é implantação institucional. Critérios que dependem de inferência podem permanecer pendentes com providers desabilitados; não são convertidos em zero.

Entrada: `http://127.0.0.1:8010/`. Professor: `/#teacher/home`; Aluno: `/#student/home`; Gestão: `/#management/home`; correção: `/tme`. Selecionar um módulo não concede permissões institucionais. Ver [operação do piloto](docs/PILOTO_10_DEZEMBRO.md) e [guia de colaboração](docs/collaboration/README.md).

**Estudo autônomo e atividades institucionais exigem sessão autenticada.** O launcher acima desabilita autenticação e não serve para testar esses fluxos. Para eles, use o [ambiente autenticado de desenvolvimento](docs/collaboration/README.md#dynamic-com-sessão-autenticada). O [estado atual do DYNAMIC](docs/collaboration/DYNAMIC_STATUS.md) reúne os três contextos e as limitações; o [relatório de consolidação I6+6B](docs/audits/CONFIA_DYNAMIC_INTERVENCOES_6_6B_CONSOLIDACAO.md) registra revisão, testes e prontidão experimental.

A preparação da candidata DYNAMIC foi preservada, sem criar tag: [manifesto e limites](docs/audits/DYNAMIC_RC1_CANDIDATE.md). Ela identifica o código `fc6f271`, anterior às correções de navegação integradas. Para conferir essa referência histórica no clone atual, execute `python3 scripts/evaluation/verify_dynamic_rc1_reference.py`. Isso verifica bytes, não declara que o checkout atual possui o fingerprint da candidata. Consulte o [relatório de consolidação](docs/audits/CONFIA_MAIN_CONSOLIDATION_2026_12.md).

## Evidência e reprodução

A RC1 é o commit `c03403fe5b83d9db9df172882bd69af3dfa2d027`. P1 tem replay offline 17/20 com respostas GPT arquivadas; P2–P5 têm 20/20 em execuções integradas sobre fixtures estruturadas. Isso **não valida soluções independentes, captura manuscrita ou correção oficial do torneio**. Lean tem cobertura parcial, não formalização global dos cinco problemas.

- [Recibo do congelamento e recuperação do bundle](docs/collaboration/RC1_RECORD.md).
- [Manifesto e relatório históricos da candidata](docs/audits/SPECIALIZED_TME2_RC1.md).
- [Protocolo de avaliação independente](docs/audits/SPECIALIZED_TME2_RC1_GOLD_PROTOCOL.md).
- [Inventário das frentes e mudanças preservadas](docs/collaboration/INVENTORY.md).
- [Contribuir sem modificar a referência congelada](CONTRIBUTING.md).

Os documentos da candidata descrevem a preparação anterior ao commit e foram preservados literalmente. O recibo acima registra o estado posterior. O bundle não está no Git; solicitar transferência controlada ao mantenedor e verificar seu hash.

## Piloto de correção ConfIA

A interface dedicada de dupla entrada está em `/tme`, autenticada por padrão para usuários `TEACHER`.
Para apresentação local, `CONFIA_TME_DEMO_NO_AUTH=1` libera somente o fluxo TME;
a flag é rejeitada em produção e não muda o acesso aos módulos escolares.
Ela aceita escrita digital no caderno existente e fotos multipágina com
originais preservados, convergindo na mesma transcrição aceita e auditoria.
A apresentação usa **ConfIA — Confiabilidade e Explicabilidade**, com a identificação
discreta **PILOTO ConfIA** e os tokens da identidade visual existente. O caderno
mantém enunciado e ferramentas de escrita visíveis durante a rolagem.
Consulte [docs/TME_PILOT_01.md](docs/TME_PILOT_01.md) para arquitetura, operação,
limitações e credenciais necessárias ao OCR real.
