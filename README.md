# ConfIA — Confiabilidade e Explicabilidade

Plataforma experimental de correção matemática, resolução assistida e acompanhamento pedagógico. Backend Python/FastAPI, frontend HTML/CSS/JavaScript e verificações formais locais com Lean.

| Frente | Situação em 25/11/2026 | Referência |
| --- | --- | --- |
| SPECIALIZED | RC1 experimental congelada; avaliação independente com gold humano pendente | Tag `SPECIALIZED-TME2-RC1` |
| DYNAMIC | Fluxo integrado de questões inéditas, rubricas, Grader, Reviewer e Reconciliation; desenvolvimento e validação continuam | Branch `codex/dynamic-development` |
| Interface | Professor baseado no TME²; entrada, Aluno e Gestão harmonizados | Branch `codex/interface-review` |
| Colaboração | Instalação, limites, inventário e orientações para revisão | Branch `codex/collaboration-handoff` |

A `main` permanece preservada. As branches de trabalho não significam aprovação para produção nem devem ser integradas automaticamente. O vídeo institucional é um projeto separado em `codex/interface-video`, com exemplos ilustrativos.

## Começar

```sh
git clone https://github.com/rmarcolinob/confia-lean-auditor.git
cd confia-lean-auditor
git switch --track origin/codex/collaboration-handoff
python3 -m venv .venv
.venv/bin/python -m pip install -e .
env -u OPENAI_API_KEY CONFIA_SEMANTIC_LLM_ENABLED=0 CONFIA_DYNAMIC_LLM_ENABLED=0 \
  .venv/bin/python scripts/pilot_dec10.py --port 8010
```

Instalar dependências pode acessar a rede. O launcher inicia **demonstração local em 127.0.0.1**, com armazenamento próprio e sem habilitar providers pagos. Não é implantação institucional. Critérios que dependem de inferência podem permanecer pendentes com providers desabilitados; não são convertidos em zero.

Entrada: `http://127.0.0.1:8010/`. Professor: `/#teacher/home`; Aluno: `/#student/home`; Gestão: `/#management/home`; correção: `/tme`. Selecionar um módulo não concede permissões institucionais. Ver [operação do piloto](docs/PILOTO_10_DEZEMBRO.md) e [guia de colaboração](docs/collaboration/README.md).

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
