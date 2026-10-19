/* TUTORIA-CHAT-DEMO-01: illustrative conversations, never learning evidence. */
(function tutorChatDemoData() {
  "use strict";
  window.ConfIATutoriaChatDemo = Object.freeze({
    origin: "DEMO",
    quickPrompts: [
      { id: "hint", label: "Me dê uma pista" },
      { id: "explain", label: "Explique de outro jeito" },
      { id: "start", label: "Como começo?" },
      { id: "reasoning", label: "Meu raciocínio faz sentido?" },
    ],
    replies: {
      content: {
        explain: "Vamos usar uma situação concreta. Que parte da ideia parece mais difícil: o significado, a representação ou a aplicação?",
        hint: ["Procure as palavras principais da definição. O que cada uma quer dizer?", "Tente criar um exemplo pequeno e conferir se ele atende à definição. Qual seria seu primeiro exemplo?"],
        start: "Comece dizendo, com suas palavras, o que você já entende do conteúdo. Qual ponto ainda gera dúvida?",
        reasoning: "Vamos explicar a ligação entre suas ideias. Que exemplo ajudaria a testar o que você está pensando?",
        example: "Podemos construir um exemplo juntos. Que valores simples você escolheria para representar essa ideia?",
        fallback: "Vamos explorar sua dúvida por etapas. Qual parte do conteúdo você gostaria de explicar com suas próprias palavras primeiro?",
      },
      functions: {
        explain: String.raw`Imagine uma quantidade que começa em \(b\) e varia sempre \(a\) por unidade. Em \(y=2x+1\), a saída começa em 1 e aumenta 2 quando \(x\) aumenta 1. O que mudaria se o 2 fosse negativo?`,
        hint: [String.raw`Compare duas entradas consecutivas em \(y=2x+1\). Quanto a saída muda?`, "Observe o valor da saída quando a entrada é zero. Qual coeficiente fica visível nessa situação?"],
        start: "Separe duas ideias: o valor inicial e a variação por unidade. Qual delas você identifica primeiro na expressão?",
        reasoning: "Vamos testar sua ideia com duas entradas. A diferença entre as saídas combina com a taxa de variação que você identificou?",
        example: String.raw`Em um exemplo diferente, \(g(x)=3x+2\). Antes de calcular, o que você espera que aconteça com a saída ao aumentar a entrada em uma unidade?`,
        fallback: "Podemos olhar a fórmula, uma tabela ou um gráfico. Qual dessas representações ajudaria você a explicar sua dúvida?",
      },
      question: {
        explain: "Vamos recontar o enunciado com suas palavras. O que ele informa e o que pede para descobrir?",
        hint: ["Escolha uma informação do enunciado e diga a que grandeza ela se refere. Como ela pode se relacionar com o que foi pedido?", "Represente a grandeza desconhecida por uma letra. Qual condição do problema poderia virar uma igualdade ou uma relação?"],
        start: "Vamos identificar primeiro os dados e a pergunta. Qual informação parece relacionar as grandezas do problema?",
        reasoning: "Explique por que escolheu esse primeiro passo. Ele usa alguma condição do enunciado? Vamos conferir essa ligação antes de seguir.",
        example: String.raw`Como exemplo de estratégia, pense em uma quantidade que aumenta 10%. Se o valor inicial for \(n\), como você representaria apenas o aumento?`,
        fallback: "Vamos relacionar sua observação ao enunciado. Que informação sustenta o próximo passo que você quer fazer?",
      },
      attempt: {
        explain: "Leia uma transformação de cada vez. Que operação você fez e por que ela pode ser usada nessa etapa?",
        hint: ["Escolha duas linhas consecutivas e confira os sinais. A operação mantém a relação entre os dois lados?", "Use valores simples para testar a transformação. Você consegue explicar o que deve permanecer igual?"],
        start: "Comece pela primeira linha que gera dúvida. O que você queria descobrir ou simplificar naquele ponto?",
        reasoning: "Vamos examinar a passagem entre duas linhas. Qual operação foi aplicada? Confira os sinais e explique por que a relação se mantém.",
        example: String.raw`Em outro exemplo, \(x+4=9\). Que operação você aplicaria nos dois membros para isolar \(x\)? Compare a estratégia com sua tentativa.`,
        fallback: "Escolha um passo da tentativa e descreva sua intenção. Que justificativa você daria para essa transformação?",
      },
    },
    angularCoefficient: String.raw`O coeficiente angular indica quanto \(y\) varia quando \(x\) aumenta uma unidade. Você prefere observar essa variação em uma fórmula ou em um gráfico?`,
  });
})();
