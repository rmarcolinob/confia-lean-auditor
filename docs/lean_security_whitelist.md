# Segurança da camada Lean — whitelist de expressões formais

## 1. Objetivo

Este documento descreve a política de segurança usada pelo `confia-lean-auditor` ao converter passos extraídos de soluções matemáticas em arquivos Lean.

O princípio central é:

> O aluno, a solução textual e a LLM nunca escrevem código Lean livre.  
> Eles só podem produzir candidatos de uma linguagem intermediária restrita, que é validada antes de qualquer execução pelo Lean.

Esta política pertence às seguintes camadas do ConfIA:

- camada Lean/formalização;
- camada de engenharia;
- camada de governança e ética;
- camada de avaliação.

---

## 2. Modelo de ameaça

O sistema recebe soluções abertas em linguagem natural. Essas soluções podem conter:

- texto matemático legítimo;
- erros algébricos;
- comandos maliciosos;
- tentativas de injeção Lean;
- strings produzidas por LLM;
- símbolos ambíguos como `D`, `Área`, `det`, `by`, `theorem`, `import`.

Como a LLM atua como extrator semântico, ela também pode produzir saídas inesperadas, incompletas ou malformadas.

A política de segurança assume que:

1. a entrada textual não é confiável;
2. a saída da LLM não é confiável;
3. apenas expressões validadas por whitelist podem ser usadas na geração de arquivos Lean;
4. o Lean verifica a validade matemática dos teoremas gerados, mas não deve ser exposto a código livre vindo do usuário ou da LLM.

---

## 3. Fronteira de segurança

A fronteira principal está no módulo:

```text
app/confia_lean_auditor/lean/safe_formal_step.py
MD


## Atualização — aritmética inteira linear

A whitelist também permite a tática `omega` para formal steps restritos de aritmética inteira linear, como argumentos de paridade e impossibilidade de equações do tipo `11 - 2*i - 2*j = 0`.

Mesmo nesse caso, o aluno e a LLM não escrevem Lean livre. As expressões continuam passando por `safe_formal_step.py`, com identificadores explicitamente permitidos, como `a`, `i` e `j`, além de numerais e operações aritméticas básicas.
