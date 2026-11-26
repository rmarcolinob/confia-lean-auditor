# R1: diagnóstico anterior à implementação

Forense congelada em `5aa7344`; baseline aplicação DY7 `e097589`. Nenhum arquivo app foi alterado antes deste protocolo/dataset.

- CLAIM_EXTRACTION: grader.extract compara shape textual; shape remove parênteses numéricos mas não faz associação estrutural entre operação, valor e expressão original. ARITHMETIC VERIFIED perde vínculo com SUBSTITUTION.
- SUFFICIENCY: grader.grade exige tag factorization mais ROOTS completo ou fórmula completa. Regex de fatoração não entende árvore com parênteses internos. Uma transformação equivalente verificada com conclusão completa pode satisfazer rubrica orientada a processo; técnica específica e crédito parcial devem respeitar obrigações explícitas.
- Arquivos a mudar: dynamic/grader.py, grading_models.py, novos módulos de representação/sufficiency/versões e emissão de contexto atual. Não mudar reviewer/reconciliation/policy para compensar o grader.
- Conservação: checker exact-polynomial existente; fonte/span intactos; inferir somente avaliação vinculada estruturalmente, nunca conclusão de solução completa a partir de conta numérica.
- DEV_V2: 40 substitution, 32 method, 4 fronteiras (função/sistema), 4 casos novos de adjudicação. 36 pares positivo/negativo primários. Numeric gold sintético, não independente. Específica fórmula e domínios não suportados continuam métricas de cobertura, sem relaxar rubrica.
- Próximos passos obrigatórios: baseline DY7 somente DEV_V2; primeiro fix/subset substituição e gate; só então método e avaliação pareada final.
