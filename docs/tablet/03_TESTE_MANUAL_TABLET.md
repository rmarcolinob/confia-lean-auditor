# ConfIA — registro de teste real da captura

Status inicial de todos os itens: NÃO EXECUTADO.
Este roteiro verifica captura e recuperação; não mede correção matemática nem precisão de OCR.

## Identificação técnica

Data:
Responsável:
Modelo do tablet:
Caneta:
Sistema/versão:
Navegador/versão:
Versão/commit do protótipo:
Conexão/URL local usada:

Usar questões e soluções de teste, sem nome/matrícula de estudante.

## Operações

| Teste | Resultado esperado | Resultado observado | Evidência |
|---|---|---|---|
| Caneta | Traços aparecem onde escritos | NÃO EXECUTADO | |
| Palma antes da caneta | Não produz tinta involuntária | NÃO EXECUTADO | |
| Palma durante escrita | Sem tinta acidental/perda silenciosa | NÃO EXECUTADO | |
| Caneta levantada/reposta | Traços distintos, sem ligação espúria | NÃO EXECUTADO | |
| Fração, expoente e menos | Detalhes preservados visualmente | NÃO EXECUTADO | |
| Borracha | Traço apagado some no estado final | NÃO EXECUTADO | |
| Desfazer/refazer | Estado recuperado exatamente | NÃO EXECUTADO | |
| Troca de página | Nenhum traço migra de página | NÃO EXECUTADO | |
| Troca de questão | Rascunho anterior preservado | NÃO EXECUTADO | |
| Rotação | Mesma geometria e conteúdo | NÃO EXECUTADO | |
| Recarregar página | Operações concluídas recuperadas | NÃO EXECUTADO | |
| Snapshot local | Editar nova versão não muda a anterior | NÃO EXECUTADO | |
| Exportar JSON | Schema aceita e conserva traços ativos | NÃO EXECUTADO | |
| Exportar PNG | Mesma escrita da versão escolhida | NÃO EXECUTADO | |
| Falha de armazenamento | Aviso, sem falsa confirmação de salvamento | NÃO EXECUTADO | |
| Rede indisponível | Não mostrar entrega ao professor | NÃO EXECUTADO | |

## Escritas para inspeção visual

Escrever propositalmente trechos corretos e incorretos; a captura não deve corrigir nenhum:

- `2025 - 1012 = 1014`
- `x^14 = 1 - x`
- `Se n é ímpar, n = 2k + 1.`
- `x ≠ 0`, `x ≤ 0`, `x < 0`
- uma fração com numerador/denominador de várias letras;
- um trecho riscado e uma versão nova ao lado.

O teste é a fidelidade do desenho/recuperação, não a validade matemática dessas afirmações.

## Conclusão do ensaio

Aprovado para próxima etapa técnica:
Falhas bloqueantes:
Limitações conhecidas:
Artefatos JSON/PNG anexados:

Nunca concluir “compatível com todos os tablets” a partir desses ensaios.
