# Transcrição docente: documento e edição

## Princípio da transcrição ConfIA

A transcrição reconhecida é uma **versão digitada fiel** da solução: legível,
matematicamente estruturada, semanticamente fiel e adequada à conferência humana
e ao Auditor ConfIA. A fidelidade se refere ao conteúdo e à ordem lógica das
etapas. A transcrição não tem como objetivo reproduzir geometricamente a folha
nem produzir um fac-símile do manuscrito.

Preservar obrigatoriamente:

- números, sinais, expoentes e índices;
- frações, funções e variáveis;
- igualdades e desigualdades;
- texto explicativo e ordem lógica das etapas;
- erros matemáticos efetivamente escritos pelo aluno.

Não é obrigatório reproduzir posição x/y, tamanho da letra, espaçamento físico,
alinhamento gráfico idêntico ou aparência manuscrita. Coordenadas e referências
históricas continuam preservadas como dados de origem, sem determinar a
diagramação da coluna de leitura.

A apresentação pode melhorar **somente a diagramação**: separar parágrafos,
apresentar fórmulas isoladas em blocos, renderizar matemática com KaTeX e preservar
quebras lógicas de linha. Essas mudanças não autorizam simplificar expressões,
trocar sinais ou números, completar etapas, reordenar o raciocínio ou corrigir a
matemática. Se o aluno escreveu `2 + 2 = 5`, a transcrição deve manter
`2 + 2 = 5`.

A edição humana corrige erros de leitura para corresponder ao que foi escrito.
Conferir confirma essa fidelidade sem atestar a correção matemática da solução.

## Fonte canônica

A view e o editor usam a mesma projeção, por segmento:

1. `latex` preenchido (campo que recebe `latex_styled` do Mathpix).
2. Na ausência de `latex`, `text`.

Os dois campos são representações alternativas. Nunca são concatenados, mesmo
quando diferem em espaços, delimitadores ou notação. Não se tenta deduplicar por
similaridade matemática. Partes complementares em **segmentos distintos** mantêm
a ordem lógica registrada em `page_index` e `order`, inclusive repetições
intencionais; a view não usa coordenadas x/y para diagramar o documento. Os campos
originais continuam consultáveis nos detalhes técnicos da revisão.

A duplicação anterior ocorria porque a view começava por `text` e acrescentava
`latex` quando não reconhecia uma cópia. A comparação cobria igualdade literal e
fórmulas delimitadas, mas não `2 + 2 = 5` versus `2+2=5`, por exemplo.

O renderer compartilhado `ConfiaRecognitionView.renderMathText`/KaTeX apresenta
prosa e matemática inline/display, sem corrigir sinais, números ou equações.
Fórmulas sem delimitadores no campo `latex` (ou em segmento matemático) recebem
`\[...\]` apenas na projeção do documento/editor. Delimitadores inválidos têm
fallback literal. A leitura não faz POST nem modifica dados, hashes ou provenance.

## Edição e revisões

“Editar transcrição” substitui a página branca por um único textarea de fonte.
Em manuscritos com várias páginas, um seletor troca a página editada sem perder os
rascunhos das demais. Os trechos de uma página são separados por uma linha em
branco no editor. Não se edita HTML gerado pelo KaTeX.

- **Cancelar:** descarta todos os rascunhos locais e volta à revisão persistida.
- **Salvar nova versão:** usa `POST /transcriptions/{id}/revisions`, baseado na
  revisão corrente, com `status: NEEDS_REVIEW`. Na primeira transcrição manual,
  usa a criação já existente em `/submissions/{id}/transcriptions`.
- Cada página editada passa a ter uma única fonte em `text`, com seus delimitadores
  LaTeX, `kind: mixed` e `latex: null`. Isso impede que uma representação antiga
  prevaleça sobre a edição. Páginas não editadas enviam seus segmentos originais
  integralmente, incluindo strings, tipos, coordenadas e referências.
- Novos trechos manuais não herdam confidence ou coordenadas medidas para trechos
  anteriores. Esses dados permanecem nas revisões históricas. O store existente
  preserva a provenance da transcrição ao criar a revisão.
- Textareas normalizam CRLF para LF na projeção; isso não reescreve páginas não
  editadas. Uma página editada admite até 20.000 caracteres, o limite existente por
  campo de segmento. Excesso mantém o rascunho e mostra um erro antes do envio.
- Após salvar, a UI busca o histórico atualizado, sai da edição e exibe a nova
  revisão como documento. Falhas de transporte/conflito mantêm o rascunho.

“Conferir transcrição” envia somente o número da revisão corrente e os dados do
aceite. Alterações não salvas bloqueiam a conferência e a análise. Uma edição
posterior a ACCEPTED cria outra revisão NEEDS_REVIEW, que precisa de novo aceite.
Revisões, acceptances e recibos anteriores não são regravados. O significado do
aceite continua sendo fidelidade ao manuscrito, sem avaliar correção matemática.

O histórico recolhível resume número, data/hora, origem automática/manual e status.
“Ver revisão” expande o documento antigo e seus detalhes técnicos. Revisões manuais
de uma transcrição originalmente automática aparecem como “Manual”.

## Verificação

`tests/js/test_teacher_transcription_view.cjs` cobre a fonte canônica, a duplicação
com notações diferentes, renderização, fonte única, múltiplas páginas, Cancelar,
salvar/aceitar/editar novamente, histórico e preservação de dados originais.
Os testes existentes de transcrições verificam a imutabilidade dos arquivos e
recibos no backend; as suítes de auditoria e TeacherDecision verificam a continuidade
do workflow. Nenhum contrato de backend foi alterado neste ajuste.
