# Dezembro — checklist de reunião

[Checklist imprimível de uma página](DEMO_DECEMBER_CHECKLIST.pdf).

**Escopo:** ensaio local, dados sintéticos, sem login; SHADOW_EVALUATION. Nunca usar dados pessoais ou publicar este servidor. Prova controlada com Q1–Q3; o motor calcula as sugestões.

## 24 horas antes

- [ ] Usar o worktree `~/Documents/confia-lean-auditor-tme-december-integration`; registrar `git rev-parse HEAD` e `git status --short`.
- [ ] Confirmar venv `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`. Para outra máquina, definir `CONFIA_DEMO_PYTHON`.
- [ ] Preparar `.lake/packages` no commit fixado em `lake-manifest.json`. Nesta máquina foi usado o cache local já compilado do repositório principal: `cp -cR ../confia-lean-auditor/.lake/packages/. .lake/packages/` (destino vazio; não sobrescrever cache divergente).
- [ ] Executar **antes da reunião** `lake build ConfiaLeanAuditor`. Se não houver cache local: preparar as dependências fixadas e executar `lake exe cache get` fora da reunião (exige rede); conferir que manifest/toolchain não mudaram e depois fazer o build. Nunca atualizar versões para resolver um erro de ambiente.
- [ ] Rodar `scripts/demo_december.sh check`; confirmar Lean 4.28.0, Mathlib `8f9d9cff6bd728b17a24e163c9402775d9e6a365` e prova formal local OK.
- [ ] Rodar os dois testes formais focais indicados no relatório e ensaiar uma análise com Lean. Guardar evidências. Não baixar nem compilar durante a reunião.

## 1 hora antes

- [ ] Fechar processos antigos na porta 8765; não matar um backend com auditoria em andamento.
- [ ] Copiar `runtime/demo_december` para backup **com backend parado**. Para ensaio limpo, usar outro diretório via `--data-dir runtime/demo_december_reuniao`; não apagar histórico.
- [ ] Iniciar, a partir do worktree: **`scripts/demo_december.sh start`**.
- [ ] Abrir **http://127.0.0.1:8765/tme**. O script fixa PYTHONPATH, flags demo/certificação, autenticação das outras áreas e bind local. Nenhuma credencial é necessária no percurso manual; OCR/API é opcional e não faz parte do percurso principal.
- [ ] Conferir assessment **“Dezembro - ensaio controlado Q1-Q3”**, ID `asmt_dec20260000000000000000000000001`. Testar desktop e janela menor. Reservar tempo para Lean; não executar build ou suítes concorrentes durante a apresentação.

## Sequência da demonstração

1. Nova correção → assessment acima → código **DEZ-ENSAIO-001** → `examples/demo_december/prova-demo.pdf` (4 páginas). Associar Q1 às páginas 1–2, Q2 à 3, Q3 à 4.
2. Q1: Original → Transcrição → Digitar. Colar `q1-inicial.txt`, dividido antes de `[c]` entre as duas páginas; salvar. Comparar; analisar e mostrar pauta/evidências.
3. Q2: digitar `q2-parcial.txt`, salvar e analisar. Voltar a Q1, corrigir apenas **584 → 594**, salvar; mostrar stale, reanalisar somente Q1 e comparar scores anterior/atual.
4. Aceitar Q1. Em Q2, ajustar para **18**, justificando “Ensaio: ajuste humano independente”. Q3: digitar `q3-erro.txt`, analisar e aceitar. Mostrar o erro matemático preservado no original.
5. Resumo → finalizar → mostrar ConfIA × humano. Reabrir correção → Q1 → reabrir questão → ajustar para **19**, justificar → finalizar v2 → abrir histórico v1/v2.
6. Certificação → mostrar SHADOW e ausência de gold → importar `gold-teste.csv`, fonte **synthetic-rehearsal**, versão **v1** → conferir métricas → baixar CSV e JSON. Gold é sintético para ensaio, não correção oficial.

## Plano B e recuperação

- Lean indisponível: parar com segurança e iniciar **`scripts/demo_december.sh start --without-lean`**. É o modo já existente; anunciar que novas auditorias não executam Lean. Preservar e identificar análises formais anteriores. Não apresentar fallback como certificado formal.
- OCR/API indisponível: usar as transcrições controladas acima e conferir no original; não inventar saída de OCR nem resultados de motor.
- Reload ou aba fechada: abrir `/tme`, localizar **DEZ-ENSAIO-001** em provas recebidas; retomar questão/resumo. Somente rascunhos ainda não salvos podem se perder. Registrar a URL da prova após recebimento.
- Backend parado: repetir o mesmo comando e **o mesmo `--data-dir`**. Captura, leituras salvas, análises, decisões, fechamentos e gold permanecem em disco. Em conflito 409, recarregar e conferir a versão antes de reenviar.
