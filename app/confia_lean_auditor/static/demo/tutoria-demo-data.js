/* TUTORIA-DEMO-01: presentation fixtures only. Never write these to institutional stores. */
(function tutorDemoData() {
  "use strict";
  const lesson = (id, title, description, example) => ({ id, title, description, example });
  window.ConfIATutoriaDemo = Object.freeze({
    origin: "DEMO",
    modules: [
      { id: "content", title: "Conteúdos", icon: "Aa", state: "DEMO", description: "Explore temas, explicações, exemplos e materiais de estudo." },
      { id: "questions", title: "Banco de questões", icon: "?", state: "REAL", description: "Encontre problemas do catálogo e escolha sua próxima prática." },
      { id: "practice", title: "Resolver questões", icon: "✎", state: "REAL", description: "Pratique no caderno e confira a leitura da sua solução." },
      { id: "feedback", title: "Feedback pedagógico", icon: "↗", state: "DEMO", description: "Revise suas tentativas e explore orientações para avançar." },
      { id: "trails", title: "Trilhas de aprendizagem", icon: "→", state: "DEMO", description: "Percursos organizados para desenvolver habilidades específicas." },
      { id: "progress", title: "Meu progresso", icon: "▥", state: "DEMO", description: "Acompanhe temas estudados, atividades e evolução." },
    ],
    future: { recommendations: "FUTURE", catalogMetadata: "FUTURE", persistentAttempts: "FUTURE" },
    topics: [
      { id: "algebra", title: "Álgebra", description: "Representar relações, transformar expressões e construir argumentos.", lessons: [
        lesson("equations", "Equações do 1º grau", "Reconheça a incógnita e mantenha a igualdade ao operar nos dois membros.", String.raw`Em \(3x+2=11\), subtraia 2 dos dois membros. Depois, divida por 3: \(x=3\). Confira por substituição.`),
        lesson("systems", "Sistemas lineares", "Relacione duas condições e compare estratégias de substituição e eliminação.", String.raw`Se \(x+y=7\) e \(x-y=1\), somar as equações resulta em \(2x=8\). Assim, \(x=4\) e \(y=3\).`),
        lesson("polynomials", "Polinômios", "Organize termos e observe o papel dos coeficientes e dos expoentes.", String.raw`Em \(p(x)=x^2-3x+2\), temos \(p(2)=4-6+2=0\). Que relação isso tem com o fator \(x-2\)?`),
      ] },
      { id: "functions", title: "Funções", description: "Conectar situações, tabelas, expressões e gráficos.", lessons: [
        lesson("function-concept", "Conceito de função", "Relacione cada elemento do domínio a um único valor de saída.", String.raw`A regra \(f(x)=2x+1\) associa \(x=0\) a 1 e \(x=2\) a 5. A entrada e a saída têm papéis diferentes.`),
        lesson("affine", "Funções do 1º grau", "Interprete uma taxa de variação constante e relacione a expressão ao gráfico.", String.raw`Na função \(f(x)=2x+1\), cada aumento de 1 em \(x\) aumenta a saída em 2.

\[f(0)=1,\quad f(1)=3,\quad f(2)=5\]

O coeficiente 2 indica a taxa de variação. O termo 1 é o valor da função quando \(x=0\).`),
        lesson("graphs", "Interpretação de gráficos", "Leia escalas, identifique variáveis e compare a variação de grandezas.", "Antes de interpretar uma curva, identifique o que cada eixo representa, as unidades e a escala. Descreva um intervalo de crescimento com suas próprias palavras."),
      ] },
      { id: "geometry", title: "Geometria", description: "Investigar formas, medidas e relações no plano.", lessons: [
        lesson("angles", "Ângulos", "Compare aberturas e reconheça relações entre ângulos.", String.raw`Dois ângulos suplementares somam \(180^\circ\). Se um mede \(65^\circ\), o outro mede \(115^\circ\).`),
        lesson("triangles", "Triângulos", "Use propriedades para relacionar lados, ângulos e áreas.", String.raw`A área de um triângulo é \(A=\frac{bh}{2}\). A altura deve ser perpendicular à base escolhida.`),
        lesson("polygons", "Polígonos", "Explore regularidades e decomponha figuras em partes conhecidas.", String.raw`Traçar diagonais a partir de um vértice de um pentágono convexo forma 3 triângulos. A soma dos ângulos internos é \(3\cdot180^\circ=540^\circ\).`),
      ] },
      { id: "trigonometry", title: "Trigonometria", description: "Relacionar ângulos, medidas e fenômenos periódicos.", lessons: [
        lesson("sine-cosine", "Seno e cosseno", "Identifique catetos e hipotenusa em relação ao ângulo escolhido.", String.raw`No triângulo retângulo, \(\sin\theta=\frac{\text{cateto oposto}}{\text{hipotenusa}}\) e \(\cos\theta=\frac{\text{cateto adjacente}}{\text{hipotenusa}}\).`),
        lesson("trig-relations", "Relações trigonométricas", "Conecte as razões trigonométricas por meio de identidades.", String.raw`A relação \(\sin^2\theta+\cos^2\theta=1\) pode ajudar a encontrar uma razão a partir da outra. Observe o quadrante antes de escolher o sinal.`),
      ] },
      { id: "statistics", title: "Estatística e Probabilidade", description: "Organizar dados e raciocinar sobre a incerteza.", lessons: [
        lesson("data", "Leitura e organização de dados", "Compare distribuições e interprete medidas de tendência central.", String.raw`Para os valores 2, 4 e 9, a média é \(\frac{2+4+9}{3}=5\). A mediana é 4. Por que as duas medidas são diferentes?`),
        lesson("probability", "Probabilidade", "Descreva resultados possíveis e explicite as hipóteses de um experimento.", String.raw`Em um dado equilibrado, há 3 resultados pares entre 6 possíveis. Assim, \(P(\text{par})=\frac{3}{6}=\frac{1}{2}\).`),
      ] },
    ],
    featured: { lessonId: "affine", topic: "Funções", minutes: 15, level: "Introdução", objectives: ["Interpretar os coeficientes da função", "Relacionar expressão, tabela e gráfico", "Explicar a taxa de variação"] },
    recommendations: [
      { title: "Revisar funções", description: "Retome a relação entre entrada, saída e taxa de variação.", destination: "content", lessonId: "affine" },
      { title: "Praticar interpretação de gráficos", description: "Observe eixos, escalas e intervalos de crescimento.", destination: "content", lessonId: "graphs" },
      { title: "Resolver 5 questões de fixação", description: "Exemplo de uma meta de estudo para uma próxima sessão.", destination: "questions" },
    ],
    trails: [
      { title: "Fundamentos de Álgebra", completed: 2, steps: ["Expressões e padrões", "Equações do 1º grau", "Sistemas lineares", "Prática no banco"], topic: "algebra" },
      { title: "Funções", completed: 1, steps: ["Conceito de função", "Função afim", "Interpretação de gráficos", "Prática no banco"], topic: "functions" },
      { title: "Geometria Plana", completed: 0, steps: ["Ângulos", "Triângulos", "Polígonos", "Prática no banco"], topic: "geometry" },
      { title: "Preparação para resolução de problemas", completed: 1, steps: ["Compreender o enunciado", "Planejar uma estratégia", "Registrar o raciocínio", "Revisar a solução"], topic: "algebra" },
    ],
    progress_demo: { studiedTopics: 3, activities: 8, questions: 5, themes: [
      { title: "Álgebra", percent: 60 }, { title: "Funções", percent: 35 }, { title: "Geometria", percent: 20 },
    ] },
    activities_demo: [
      { title: "Funções do 1º grau", detail: "Leitura de conteúdo · exemplo de atividade", destination: "content", lessonId: "affine" },
      { title: "Uma tentativa, novas estratégias", detail: "Prática e revisão · exemplo de atividade", destination: "feedback" },
    ],
    feedback_demo: {
      title: "Exemplo de revisão · Função afim",
      solution: String.raw`Para \(f(x)=2x+1\), calculei:
\[f(3)=2\cdot3+1=7\]
A saída aumenta em 2 quando a entrada aumenta em 1.`,
      positive: "Neste exemplo, a substituição e a taxa de variação estão registradas com clareza.",
      review: "Relacione a expressão a uma tabela e explique o significado de cada coeficiente.",
      next: "Calcule a saída para outras entradas e represente os pares em um gráfico.",
    },
    practice_guidance_demo: {
      positive: "Você registrou uma tentativa. Esse registro permite revisitar seu raciocínio.",
      review: "Compare as etapas com o enunciado e confira sinais, operações e hipóteses usadas.",
      next: "Explique por que cada transformação é válida e experimente uma nova tentativa.",
    },
  });
})();
