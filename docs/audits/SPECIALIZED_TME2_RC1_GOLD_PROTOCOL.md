# SPECIALIZED-TME2-RC1 Protocolo inicial de avaliação com gold humano

Especificação prospectiva para avaliar soluções independentes de TME2026P1 a
TME2026P5 após o congelamento experimental. Nenhum dado gold foi coletado ou
fornecido ao corretor nesta preparação. Os resultados históricos P1–P5 são
controles de regressão e ficam fora das estimativas de acurácia desta avaliação.

## Perguntas e unidade de análise

Medir se o corretor atribui crédito conforme a pauta original, reconhece métodos
alternativos, justifica decisões com evidências do aluno e distingue abstenção
matemática de falha técnica. A unidade primária é uma solução completa de um
problema; itens e critérios são observações aninhadas nessa solução. Repetições
da mesma solução não contam como novos participantes.

A primeira fase usa texto independente revisado, com os itens explicitamente
identificados conforme o contrato de entrada existente. Não acrescentar tags
canônicas de fixtures, claims, checkers ou pistas de pontuação ao texto. Registrar
a solução original, a versão aceita e qualquer correção de transcrição, com
hashes e autoria da alteração. Uma correção deve preservar a matemática escrita.

A fase manuscrita será um estudo posterior separado. Ela exige gold de
transcrição e análise da cadeia imagem–texto–nota. Uma execução sobre texto
digitado não valida OCR, escrita no caderno ou captura de manuscrito.

## Amostra proposta

Primeira bateria: **150 soluções independentes, 30 por problema**, com seis
soluções em cada estrato primário abaixo. É um estudo inicial balanceado, não
uma estimativa da frequência dos tipos de solução no torneio.

| Estrato primário | Critério de seleção |
| --- | --- |
| Correta pelo método usual | Desenvolvimento suficiente e todos os itens corretos. |
| Parcialmente correta | Crédito parcial defensável na pauta e desenvolvimento que permita avaliar erros e acertos. |
| Matematicamente incorreta | Erros efetivos com desenvolvimento explícito; não substituir esse grupo por páginas vazias. |
| Correta por método alternativo | Argumento independente válido, sem apenas parafrasear a fixture ou o método preparado. |
| Interpretação semântica | Abreviações, justificativa verbal, dependência entre itens ou desenvolvimento não reconhecível por uma igualdade isolada; duas corretas, duas parciais e duas incorretas por problema. |

Uma solução recebe um único estrato primário, com tags secundárias quando
pertinente. Nos estratos parcialmente corretos, incluir erros de cálculo,
omissões e etapas posteriores independentemente corretas; incluir carry-forward
somente onde a pauta o prevê. Os estratos são determinados por curadores/humanos
e não enviados ao corretor.

Os autores não devem consultar fixtures, respostas arquivadas, saídas do
corretor ou relatórios de auditoria ao produzir soluções. Não usar perturbações
das fixtures como amostra independente. Registrar origem, autoria pseudonimizada,
eventual relação entre participantes e procedência de cada método. Controlar
duplicatas textuais e variantes do mesmo desenvolvimento antes do congelamento
dos dados. Soluções do mesmo autor permanecem no mesmo grupo de análise.

Um lote separado de cinco soluções, uma por problema, pode testar transporte e
observabilidade antes do holdout. Esse lote não entra nas métricas. Se o lote
levar a alteração do corretor, emitir nova candidata e refazer a identificação
da versão antes de abrir o holdout. Não ajustar código/prompt/pauta depois de
examinar seus resultados e ainda chamar o experimento de RC1.

## Construção e isolamento do gold

Dois avaliadores matemáticos corrigem independentemente cada solução usando
somente enunciado, pauta original e solução. Eles não veem saída do corretor,
modelo utilizado ou notas de referência anteriores. Um terceiro avaliador
adjudica divergências; preservar as duas avaliações iniciais e a justificativa
da adjudicação. A classificação do método alternativo deve ser explicada
matematicamente, não decidida pela concordância com o método do sistema.

Para cada item, registrar pontos, máximo, faixa/caminho aplicável e justificativa.
Para cada critério oficial, registrar atendido, não atendido ou insuficiente
para julgar, com trechos e offsets na versão aceita. Mapear critérios oficiais
aos IDs/regras da pauta congelada antes de comparar saídas. Obrigações auxiliares
de um método não utilizado recebem `not_applicable`; não as tratar como erros
do aluno nem incluí-las no denominador de concordância matemática. Guardar
separadamente pertinência do caminho, erros de cálculo, ausência de justificativa
e refutação de uma afirmação falsa. A verdade de uma proposição não substitui
a justificativa exigida pela pauta.

Ambiguidade que os humanos não conseguem resolver fica registrada como
`gold_unresolved`. Não fabricar um número para completar a tabela. Esses casos
permanecem no fluxo de amostragem e são reportados à parte; não entram no MAE
numérico, cujo denominador deve ser explícito.

O custodiante do gold mantém os arquivos em outra conta/ambiente de execução,
sem montagem no filesystem do corretor, permissão de leitura, serviço de busca,
API ou credencial acessível ao processo de correção. Separar somente diretórios
com o mesmo usuário Unix não garante isolamento. O avaliador automático recebe
apenas IDs opacos, enunciado, pauta preparada e solução aceita. Notas humanas,
estratos, justificativas gold, nomes sugestivos de arquivos e metadados de erro
não podem entrar em requests, prompts, logs de entrada ou contexto recuperado.

O processo de correção deve usar uma cópia permitida do código/assets, sem o
dataset gold, fixtures de avaliação ou relatórios com respostas da amostra.
As respostas matemáticas previstas na pauta preparada continuam autorizadas;
elas não são o gold das soluções independentes. O custodiante registra checksums
e versões do gold antes da execução. Somente após fechar e hashear todas as
saídas do corretor, um processo de análise separado junta resultados e gold
por ID. Não devolver a tabela unida ao processo de correção.

## Execução e proveniência

Fixar antes da bateria: tag/commit, SHA-256 do manifesto e bundle, fingerprint,
pautas, política, prompt/schema, modelo solicitado, esforço de raciocínio,
versões do SDK/toolchain, uso de Lean, hardware, modo de entrada e configuração
de autenticação. O perfil começa com concorrência 1 e uma execução principal
por solução, em ordem pseudoaleatória com semente 20261125 e lista de IDs
guardada pelo orquestrador. O corretor não recebe estratos nem a semente.

Não repetir até obter concordância com gold e não selecionar a melhor nota de
várias execuções. Para medir instabilidade do modelo, selecionar previamente
três soluções por problema e executar duas repetições adicionais de cada uma;
analisar essas 30 chamadas de correção adicionais separadamente. Elas dependem
de autorização/orçamento posterior. No máximo são 180 correções nesse desenho,
sem contar a quantidade variável de chamadas semânticas por correção.

Toda execução recebe ID, timestamps UTC, hash da solução aceita, hash de
requests/respostas, modelo solicitado e retornado, status, uso de tokens,
tentativas, certificados Lean, decisões por obrigação, caminhos da pauta,
pontuação e projeção diagnóstica. Guardar `needs_review` e `verdict` originais.
Registrar erros e resultados parciais inclusive quando não há nota final.

No provider atual, cada chamada tem timeout de 60 s, sem retries automáticos
do SDK e limite de 4000 tokens de saída. O checker de prova do aluno usa por
padrão orçamento de 90 s, compartilhado entre prova e refutação; outro runner
Lean genérico tem padrão de 30 s. Esses limites não representam timeout total
por solução. Não alterá-los durante a bateria. Não há temperatura nem semente
do modelo explicitamente configuradas. Alias remoto e eventual ausência de
identificador imutável devem constar como limitação de reprodução generativa.

Falha técnica não equivale a zero. Preservar a primeira tentativa na análise
primária; retomadas pertencem a análise operacional separada, com custo acumulado.
Se o cliente expirar, consultar o estado do mesmo AuditRun antes de iniciar outra
correção; expiração do transporte não prova que o servidor cancelou a execução.

## Métricas e denominadores

Publicar por problema, por item, por critério aplicável, por estrato e no total.
Dar a cada problema peso igual no resumo balanceado. Não tratar itens de uma
mesma solução como participantes independentes. Exibir contagens e intervalos
de 95%; quando usar bootstrap, reamostrar por autor/grupo e preservar a estrutura
dos problemas, com semente registrada. Com seis casos por estrato/problema,
intervalos serão amplos e não sustentam alegações de alta precisão populacional.

| Dimensão | Métricas |
| --- | --- |
| Nota final e itens | Concordância exata, MAE, MAE dividido pelo máximo, viés médio, frequências e magnitudes de sobrecrédito/subcrédito; informar denominador dos pares com gold e nota conclusivos. |
| Critérios | Matriz de confusão de atendido/não atendido, precisão e recall por classe, abstenções separadas e suporte de cada classe. Calcular sobre critérios aplicáveis; não converter `review` em não atendido. |
| Cobertura | Fração com `score_state=determined` e nota numérica entre todas as execuções; cobertura por item e critério; mostrar erro condicionado à cobertura ao lado da própria cobertura. |
| Pendências | Taxas distintas de pendência matemática relevante, falha técnica relevante, falha técnica não bloqueante, alternativa dispensável, revisão semântica e exigência humana desconhecida/conhecida. Não usar a flag legada isolada como abstenção. |
| Discordância humana | Concordância exata e diferença de pontos entre os dois avaliadores antes da adjudicação; taxa de adjudicação e gold irresolvido. Reportar comparação com cada avaliador e com o gold adjudicado. |
| Métodos alternativos | Cobertura, concordância e subcrédito no estrato alternativo; classificar falhas de representação, contrato, interpretação semântica e aplicação da pauta. |
| Justificativas | Revisão humana posterior de fidelidade das citações, validade matemática, suficiência e pertinência ao critério. Escala 0=inválida, 1=parcial, 2=adequada; reportar dimensões separadamente e dupla revisão de uma subamostra pré-selecionada. |
| Instabilidade | Variação de nota e de decisão por critério nas repetições previamente escolhidas; proporção de trocas entre decisão e abstenção. |
| Custo | Chamadas, tokens de entrada/saída/cache quando disponíveis, custo por solução e por solução concluída, acumulando falhas/retomadas e separando a bateria principal das repetições. |
| Latência | Tempo ponta a ponta em relógio monotônico; mediana, p90, p95 e máximo, com falhas/censura explícitas. Medir cliente/servidor separadamente quando observáveis e informar concorrência/cache frio ou quente. |

Em custo, arquivar a tabela de preços datada e a moeda usadas no cálculo.
Uso ou cobrança ausentes ficam desconhecidos, não zero. Antes de qualquer
execução paga, registrar teto absoluto de orçamento e condição de parada;
nenhum valor foi autorizado ou gasto nesta preparação. O custo de retomadas
não deve desaparecer do custo por solução concluída.

Latências por obrigação/componente só serão publicadas quando medidas.
`created_at` isolado não fornece duração de uma chamada; não reconstruir
tempos de GPT ou Lean por subtrações sem timestamps adequados. A observação de
tempo/custo não modifica decisões nem política matemática.

## Discordâncias e critérios de decisão

Depois do fechamento das saídas, classificar divergências por: transcrição,
extração/proveniência, evidência insuficiente, método não representado, checker,
Lean técnico, parecer semântico, seleção de caminho/pauta, projeção de estado
ou divergência humana. Preservar o texto e a cadeia de evidências; a causa não
é inferida apenas da diferença de notas. Registrar casos sem causa estabelecida.

Condições para iniciar a bateria: candidata identificada e verificável;
controles de regressão aprovados; isolamento demonstrado por contas/permissões;
amostra e gold congelados; métricas e denominadores pré-registrados;
configuração de provider, armazenamento e orçamento definidos.

Condições que invalidam a execução experimental: acesso do corretor ao gold,
mudança não registrada de código/pauta/política, alteração de fonte aceita sem
nova versão, auditoria sem identidade verificável ou perda da trilha de decisões.
Não excluir silenciosamente os casos afetados; documentar a interrupção e
reiniciar em uma versão identificada quando necessário.

Ao encerrar, todas as 150 soluções devem estar contabilizadas como concluídas,
abstenções, falhas ou gold irresolvido. Essa contabilização não exige converter
falha em nota. Não há limiar de acurácia que autorize uso oficial definido por
esta especificação inicial: a decisão exige estudo independente, análise dos
erros e critérios institucionais prévios. Resultados desfavoráveis devem ser
publicados com a mesma identificação da candidata, sem ajustar a pauta para
aproximar as notas humanas.
