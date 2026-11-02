"""Mathematical views of existing obligations. No scoring data crosses this API.

Descriptions specify roles and evidence, not a reference student's answer.
Composites expose their existing mathematical ingredients, never award rules.
"""
from confia_lean_auditor.student_claims.semantic import vocabulary
from confia_lean_auditor.tme.registry import ROOT, TME_PROBLEMS
from confia_lean_auditor.rubric.pauta import load_pauta

P1 = {
 'a.identifies_137': ('Identifica o número de algarismos invertidos.', ['expression']),
 'a.constructs_subtraction': ('Monta a subtração do número e de seu reverso.', ['expression']),
 'a.result_594': ('Escreve o resultado da subtração concreta.', ['expression']),
 'a.arithmetic_error_only': ('Apresenta uma única subtração com operandos identificados e resultado escrito; preserve a conta, sem diagnosticar sua correção.', ['expression']),
 'b.reversed_number': ('Representa o número invertido usando os dígitos e suas posições decimais.', ['expression']),
 'b.subtraction': ('Constrói a diferença entre as duas expansões decimais.', ['expression']),
 'b.middle_cancellation': ('Mostra o cancelamento dos termos do algarismo central.', ['expression']),
 'b.factorization': ('Desenvolve e fatora a diferença das representações decimais.', ['expression']),
 'c.uses_expression': ('Usa a expressão geral da diferença para obter resultados possíveis.', ['expression']),
 'c.difference_domain': ('Explicita o domínio inteiro da diferença entre os dígitos extremos e suas restrições.', ['collection','expression']),
 'c.pattern_recognized': ('Explicita uma regra ou padrão dos resultados possíveis.', ['expression','collection']),
 'd.equation': ('Iguala a expressão da máquina ao resultado pedido no enunciado.', ['expression']),
 'd.difference_six': ('Obtém a diferença entre os algarismos extremos a partir da equação.', ['expression']),
 'd.digit_pairs': ('Enumera pares de algarismos extremos, conservando a ordem declarada das variáveis.', ['collection']),
 'd.middle_choices': ('Explicita as possibilidades do algarismo central.', ['collection','expression']),
 'd.total_thirty': ('Conta as entradas da máquina a partir dos pares e das escolhas centrais.', ['expression']),
}
for key in ('complete_list','no_extraneous_values','single_list_error','several_correct','some_correct'):
 P1['c.'+key]=('Apresenta a lista de resultados possíveis. Copie a lista escrita, inclusive erros ou omissões; não julgue completude ou correção.', ['collection'])
P2 = {
 'pair_sum':'Soma dos dois números extremos de uma linha.', 'line_sum':'Soma comum de uma linha incluindo o centro.',
 'pairs':'Pares de números opostos nas linhas.', 'balance_relation':'Relação entre a soma das linhas, a soma dos números e a multiplicidade do centro.',
 'sum_formula':'Fórmula da soma comum em função do número central.', 'integral_sum':'Afirma que a soma comum é inteira.',
 'modular_condition':'Condição de divisibilidade/congruência para a soma comum ser inteira.', 'centers':'Conjunto de números centrais possíveis.',
 'admissible_center':'Um número central admissível explicitamente indicado.', 'center_sums':'Pares ordenados centro/soma comum.',
 'sum_at_five':'Soma comum quando o centro é cinco.', 'max_center':'Número central que o estudante afirma maximizar a soma.',
 'max_sum':'Maior soma comum afirmada.', 'pair_permutations':'Contagem de distribuições dos pares entre as linhas.',
 'pair_orientations':'Contagem de orientações internas dos pares nas linhas.', 'total':'Total de preenchimentos afirmado.',
 'counting_product':'Produto escrito das contagens de distribuições e orientações, com seu desenvolvimento.',
}
P3 = {
 'a.bottom_white_count':('Quantidade de bolas brancas inicialmente na base.', ['inferiores_brancas']),
 'a.first_white_probability':('Probabilidade da primeira bola ser branca.', ['primeira_branca']),
 'b.ordered_pairs':('Tamanho do espaço de pares ordenados das duas escolhas.', ['pares_ordenados']),
 'b.different_favorable':('Contagem dos pares distintos favoráveis a uma segunda bola branca.', ['favoraveis_distintos']),
 'b.same_compartment':('Conjunto de compartimentos favoráveis quando a escolha se repete.', ['repeticao_branca']),
 'b.second_white_probability':('Probabilidade da segunda bola ser branca.', ['segunda_branca']),
 'b.alternative_complete':('Argumento por condicionamento na primeira escolha e soma ponderada dos ramos.', [*(f'ramo_{i}' for i in range(1,7)),'arvore_total']),
 'c.continue_compartments':('Compartimentos da primeira escolha que permitem continuar o jogo.', ['continuar']),
 'c.total_win_probability':('Probabilidade total de vitória desenvolvida a partir dos ramos e estratégias escolhidas.', ['total']),
}
for i in (1,2):
 P3[f'c.strategy_case_{i}']=(f'Cor escolhida e sua contagem na base após retirada inicial do compartimento {i}.', [f'estrategia_{i}',f'contagem_{i}'])
 P3[f'c.conditional_success_{i}']=(f'Probabilidade de acertar a cor condicionada à retirada inicial do compartimento {i}.', [f'condicional_{i}'])
P5 = {
 'candidate':'Lista candidata para a soma do item, com valores e multiplicidades explicitamente escritos.',
 'product':'Cálculo escrito do produto da lista, incluindo fatores e igualdade com o resultado.',
 'enumeration':'Tabela de partições e seus produtos apresentada pelo estudante; não completar linhas ausentes.',
 'normal_list':'Lista na forma reduzida usada no argumento de maximalidade.',
 'one_domain':'Domínio da outra parcela usada na transformação de uma parcela igual a um.',
 'one_sum':'Igualdade mostrando preservação de soma ao combinar uma parcela um com outra parcela.',
 'one_gain':'Comparação dos produtos antes e depois de combinar a parcela um.',
 'domain':'Domínio escrito para a transformação de uma parcela grande (n≥5).',
 'sum_preserved':'Igualdade escrita mostrando preservação da soma ao substituir uma parcela por duas.',
 'increase':'Desigualdade ou comparação escrita que afirma aumento do produto na substituição.',
 'old_contribution':'Contribuição da parcela ao produto antes da substituição.',
 'new_contribution':'Contribuição das parcelas ao produto depois da substituição.',
 'four_sum':'Igualdade de somas na troca de uma parcela quatro por duas parcelas dois.',
 'four_product':'Igualdade de produtos na troca de quatro por dois dois.',
 'twos_sum':'Igualdade de somas na troca de três parcelas dois por duas parcelas três.',
 'twos_gain':'Comparação dos produtos da troca de três dois por dois três.',
 'threes_count':'Multiplicidade explícita de parcelas de valor três.',
 'twos_count':'Multiplicidade explícita de parcelas de valor dois.',
 'decomposition':'Igualdade que decompõe a soma total usando as multiplicidades afirmadas.',
 'max_product':'Expressão fatorada afirmada como produto máximo, sem calcular seu valor enorme.',
 'quotient':'Divisão euclidiana escrita da soma por três; preservar quociente e resto, mesmo se errados.',
 'list_twos':'Lista de parcelas dois e três, com multiplicidades explícitas.',
 'list_four':'Lista com parcela quatro e parcelas três, com multiplicidades explícitas.',
 'size_twos':'Quantidade de elementos da lista com dois dois.',
 'size_four':'Quantidade de elementos da lista com quatro.',
 'different_sizes':'Relação entre as quantidades de elementos das duas listas.',
}
REWRITES=['one_domain','one_sum','one_gain','domain','sum_preserved','increase','four_sum','four_product','twos_sum','twos_gain']
P5_COMPOSITES={
 'structural_max':('Argumento de maximalidade mediante transformações que preservam soma e melhoram produto, seguido de lista reduzida.', REWRITES+['normal_list']),
 'comparison':('Compara as contribuições antes e depois da substituição.', ['old_contribution','new_contribution']),
 'no_ones':('Justifica a exclusão de parcelas iguais a um mediante uma transformação que aumenta o produto.', ['one_domain','one_sum','one_gain']),
 'no_ge5':('Justifica a exclusão de parcelas grandes mediante a transformação do item b.', ['domain','sum_preserved','increase']),
 'general_rule':('Regra geral de multiplicidades para cada classe de resto da soma por três.', [f'residue{i}_{k}' for i in range(3) for k in ('twos','threes')]),
 'general_complete':('Argumento geral de redução, análise dos restos e aplicação à soma pedida.', REWRITES+[f'residue{i}_{k}' for i in range(3) for k in ('twos','threes')]+['quotient','max_product']),
 'uniqueness':('Justifica por que as formas listadas são as únicas, pela fusão dos dois dois.', ['only_forms','four_sum','four_product']),
 'sizes':('Calcula as duas quantidades de elementos e compara os tamanhos.', ['size_twos','size_four','different_sizes']),
 'cf_adoption':('Adoção explícita do resultado anterior para contar elementos.', ['cf_adopt_threes']),
 'cf_dependency':('Declara explicitamente que as contagens dependem do resultado anterior adotado.', ['cf_dependency']),
 'cf_coherence':('Desenvolvimento coerente das duas contagens a partir do resultado adotado.', ['cf_size_twos','cf_size_four','cf_different_sizes']),
}


def internal_id(problem_id):
 return 'TME2_P1_PILOT' if problem_id=='TME2026P1' else problem_id


def mathematical_obligations(problem_id):
 problem_id=internal_id(problem_id)
 config=load_pauta(ROOT/'examples/pautas'/TME_PROBLEMS[problem_id])
 vocab=vocabulary(problem_id);result=[]
 for o in config.obligations:
  key=o.id.split('.',1)[1]
  if problem_id=='TME2_P1_PILOT':desc,subjects=P1[o.id]
  elif problem_id=='TME2026P3':desc,subjects=P3[o.id]
  elif problem_id=='TME2026P2':
   if key.startswith('realizable_'):
    desc='Pares escritos que realizam a configuração para o centro indicado no identificador.';subjects=[key]
   elif key in ('placement','complete_configuration'):
    desc='Configuração de posições. Não criar DiagramState; preserve apenas descrição qualitativa se a evidência depende de posições.';subjects=['unmapped']
   else:desc,subjects=P2[key],[key]
  elif problem_id=='TME2026P4':
   # Describe roles without transmitting numeric target answers from the pauta.
   subjects=[key]
   if key.startswith('triangle_'):desc='Classificação geométrica do triângulo '+key.removeprefix('triangle_').upper()+'.'
   elif key.startswith('perimeter_'):desc='Perímetro de '+key.removeprefix('perimeter_').upper()+', com o desenvolvimento escrito quando houver.'
   else:desc={'apqr':'Classificação geométrica do quadrilátero APQR.','shaded_sum':'Soma desenvolvida dos perímetros sombreados.','exclude_12':'Equação do caso em que o perímetro fixo é hipotenusa e argumento de ausência de solução real.','h_plus_c':'Relação entre hipotenusa e outro cateto e sua soma.','pythagoras':'Relação de Pitágoras entre hipotenusa e catetos.','h':'Valor obtido para a hipotenusa.','c':'Valor obtido para o outro cateto.','shaded_lengths':'Correspondência entre os perímetros algébricos e os comprimentos calculados.','x_candidates':'Conjunto de valores de x concluídos.','case_3x':'Equação de Pitágoras com o perímetro PBQ como hipotenusa.','case_other':'Equação com o outro perímetro sombreado como hipotenusa.','case_3x_root':'Raiz obtida no caso PBQ hipotenusa.','case_other_root':'Raiz obtida no outro caso.'}.get(key,'Comprimento explicitamente atribuído ao segmento '+key.upper()+'.')
  else:
   if key in P5_COMPOSITES:desc,subjects=P5_COMPOSITES[key]
   else:
    desc=P5.get(key,'Multiplicidade explícita de parcelas para a classe de resto indicada.');subjects=[key]
   if key=='enumeration':subjects=['enumeration','enum_max']
   if key=='increase':subjects=['increase','difference','positive_difference']
  representations=[]
  for subject in subjects:
   spec=vocab.get(subject,{'kind':'qualitative' if subject=='unmapped' else 'math' if subject=='expression' else 'finite_set'})
   representations.append(dict(subject=subject,**spec))
  # Preserve pertinent prose as non-authoritative evidence when no existing
  # mathematical representation can express it. Never misreport this as absence.
  if not any(r['subject']=='unmapped' for r in representations):
   representations.append(dict(subject='unmapped',kind='qualitative'))
  result.append(dict(obligation_id=o.id,item_id=o.id.split('.')[0],description=desc,
   expected_evidence=['Trecho literal que afirma este conteúdo, inclusive contas incorretas; não completar uma prova ausente.',
    'Identifique separadamente os ingredientes explícitos; descreva ausência quando nenhum estiver escrito.'],representations=representations))
 return tuple(result)
