# Status Lean forte das questoes F2

## Padrao Lean forte operacional

Neste projeto, uma questao esta no padrao Lean forte operacional quando a rota
`/audit` consegue reconhecer etapas centrais da solucao, renderizar passos
formais, gerar um `Attempt.lean`, compilar um certificado Lean canonico, checar
afirmacoes concretas do aluno quando elas sao extraidas e devolver um relatorio
pedagogico com evidencia textual e confiabilidade.

Esse padrao e operacional: ele certifica o nucleo matematico modelado e os
claims reconhecidos pelo sistema. Ele nao significa, por si so, que todo o
enunciado original foi formalizado em Lean no nivel mais semantico possivel.

## Cobertura das cinco F2

| Questao | Certificado estatico | Verificacao dinamica | Cobertura Lean real | Limitacoes formais |
|---|---|---|---|---|
| ITA2025F2Q1 | `StrongF2Q1Claim` e `strong_f2q1_claim` | Reducoes de potencia, forma reduzida, sistema e resposta | Resto linear modulo `x^2 - x + 1`, candidato e unicidade | Modelo usa pares lineares em vez de polinomios quociente gerais. |
| ITA2025F2Q3 | `StrongF2Q3Claim` e `strong_f2q3_claim` | Diferenca beta, valores candidatos e soma final | Algebra dos candidatos, circulo unitario e selecao por sinal | Nao formaliza diretamente alpha/beta como angulos nem deriva os sinais dos intervalos do enunciado. |
| ITA2025F2Q5 | `StrongF2Q5Claim` e `strong_f2q5_claim` | Decomposicao logaritmica escalada, mantissa, limites e digito | Aritmetica escalada e certificado exato `5*10^47 <= 3^100 < 6*10^47` | Nao formaliza a teoria analitica de `log10`; os logs dados sao tratados como dados escalados. |
| ITA2025F2Q6 | `StrongF2Q6Claim` e `strong_f2q6_claim` | Formula de probabilidade, razao e resposta | Valores canonicos, identidade da razao e limiar aritmetico | Ainda nao prova uma maximizacao global completa da distribuicao a partir de uma funcao de probabilidade formal para todo `n`. |
| ITA2025F2Q8 | `StrongF2Q8Claim`/`strongF2Q8Claim` e `strong_f2q8_claim` | Formula do determinante, soma final, pares e igualdades aritmeticas | Determinante da matriz `maxMatrix`, ponte por diferencas de colunas e soma alternada final | A verificacao dinamica de formula do aluno testa familias suportadas por amostras finitas; o teorema estatico prova a formula geral canonica. |

## Quatro niveis de garantia

**Prova informal** e o texto do aluno ou da solucao de referencia. Ela pode
estar correta matematicamente, mas ainda nao foi traduzida para objetos formais
do projeto.

**Formalizacao parcial** e um recorte do argumento em Lean. Ela prova uma etapa
ou um modelo util, mas pode deixar hipoteses do enunciado, escolhas de sinal,
dominios ou ligacoes semanticas como argumentos externos.

**Certificado Lean estatico** e o `Attempt.lean` gerado a partir de claims
canonicos reconhecidos. Quando compila, ele mostra que os teoremas canonicos
necessarios para aquela solucao reconhecida passam em Lean.

**Verificacao dinamica de claim do aluno** cria pequenos teoremas a partir de
afirmacoes concretas extraidas do texto do aluno. Claims corretos compilam;
claims errados devem falhar ou ficar sem suporte, sem receber pontos extras.

## Leitura recomendada dos resultados

Um resultado `verified` no certificado estatico deve ser lido como: o nucleo
formal reconhecido para aquela questao compilou. Um `student_claim_check`
`verified` ou `failed` deve ser lido como uma decisao local sobre uma afirmacao
extraida do aluno. O relatorio pedagogico combina esses sinais com a rubrica,
mas continua dependente da cobertura dos extractors e dos tipos de claim
implementados.
