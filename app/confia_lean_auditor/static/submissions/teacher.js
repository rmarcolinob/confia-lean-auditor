(function teacherManuscripts() {
  "use strict";
  const inbox = document.querySelector("#manuscript-inbox");
  const legacy = document.querySelector("#teacher-text-prototype");
  const list = document.querySelector("#manuscript-list");
  const detail = document.querySelector("#manuscript-detail");
  const message = document.querySelector("#manuscript-message");
  const showInk = document.querySelector("#show-manuscripts");
  const showText = document.querySelector("#show-text-prototype");
  let listSequence = 0;
  let detailSequence = 0;
  const validId = (id) => typeof id === "string" && /^sub_[0-9a-f]{32}$/.test(id);
  const when = (value) => new Date(value).toLocaleString("pt-BR");

  function node(tag, content) {
    const value = document.createElement(tag);
    if (content !== undefined) value.textContent = content;
    return value;
  }

  async function read(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) throw new Error(`Consulta indisponível (HTTP ${response.status}). Tente atualizar novamente.`);
    return response.json();
  }

  async function open(id) {
    if (!validId(id)) return;
    const request = ++detailSequence;
    detail.hidden = true;
    detail.replaceChildren();
    message.textContent = "Carregando manuscrito e verificando integridade…";
    try {
      const data = await read(`/submissions/${id}`);
      if (request !== detailSequence) return;
      const record = data.submission;
      if (record.submission_id !== id) throw new Error("Registro retornado não corresponde à submissão selecionada.");
      detail.appendChild(node("h3", "Manuscrito original"));
      detail.appendChild(node("p", `submission_id: ${id}`));
      detail.appendChild(node("p", `Questão: ${record.problem_id} · Recebida em: ${when(record.received_at)} · Status: ${record.status}`));
      if (record.student_reference) detail.appendChild(node("p", `Referência não verificada (sem autenticação): ${record.student_reference}`));
      const intact = data.integrity.length === record.page_images.length + 1 && data.integrity.every((item) => item.matches);
      detail.appendChild(node("p", intact ? "Integridade técnica: hashes SHA-256 conferem." : "Alerta: há artefato ausente ou com hash divergente."));
      detail.appendChild(node("p", "Hashes indicam somente integridade técnica; não comprovam autoria nem validade matemática."));
      const hashes = node("details");
      hashes.appendChild(node("summary", "Detalhes de integridade e recibo"));
      hashes.appendChild(node("p", `snapshot_id: ${record.snapshot_id} · schema: ${record.capture_schema_version} · source: ${record.source}`));
      const items = node("ul");
      for (const artifact of data.integrity) {
        items.appendChild(node("li", `${artifact.filename}: ${artifact.matches ? "confere" : "divergente/ausente"} · SHA-256 esperado: ${artifact.expected_sha256} · atual: ${artifact.actual_sha256 || "ausente"}`));
      }
      hashes.appendChild(items);
      const download = node("a", "Baixar snapshot original (JSON)");
      download.href = `/submissions/${id}/snapshot`;
      hashes.appendChild(download);
      detail.appendChild(hashes);
      for (const page of [...record.page_images].sort((a, b) => a.page_index - b.page_index)) {
        if (!Number.isInteger(page.page_index) || page.page_index < 0 || page.page_index > 2) throw new Error("Índice de página inválido.");
        const figure = node("figure");
        figure.appendChild(node("figcaption", `Página ${page.page_index + 1} · PNG original recebido`));
        const integrity = data.integrity.find((item) => item.filename === page.filename);
        if (integrity?.matches) {
          const image = node("img");
          image.alt = `Manuscrito original da questão ${record.problem_id}, página ${page.page_index + 1}`;
          image.src = `/submissions/${id}/pages/${page.page_index}`;
          image.addEventListener("error", () => {
            figure.appendChild(node("p", "Não foi possível carregar este PNG. Atualize a consulta para conferir a integridade."));
          });
          figure.appendChild(image);
        } else figure.appendChild(node("p", "PNG indisponível por divergência de integridade."));
        detail.appendChild(figure);
      }
      detail.hidden = false;
      message.textContent = "Submissão aberta. Apenas visualização dos artefatos recebidos.";
    } catch (error) {
      if (request === detailSequence) {
        detail.replaceChildren();
        detail.hidden = true;
        message.textContent = error.message;
      }
    }
  }

  async function refresh() {
    const request = ++listSequence;
    ++detailSequence;
    detail.hidden = true;
    detail.replaceChildren();
    list.replaceChildren();
    message.textContent = "Consultando submissões recebidas…";
    try {
      const records = await read("/submissions");
      if (request !== listSequence) return;
      if (!Array.isArray(records)) throw new Error("Lista de submissões inválida.");
      for (const record of records) {
        if (!validId(record.submission_id)) continue;
        const button = node("button", `${record.problem_id} · ${record.status} · ${when(record.received_at)} · ${record.submission_id}`);
        button.type = "button";
        button.className = "secondary-action";
        button.addEventListener("click", () => open(record.submission_id));
        list.appendChild(button);
      }
      message.textContent = records.length ? `${records.length} submissão(ões) no servidor. Selecione para abrir.` : "Nenhuma submissão recebida pelo servidor.";
    } catch (error) {
      if (request === listSequence) message.textContent = error.message;
    }
  }

  function mode(manuscripts) {
    inbox.hidden = !manuscripts;
    legacy.hidden = manuscripts;
    showInk.setAttribute("aria-pressed", String(manuscripts));
    showText.setAttribute("aria-pressed", String(!manuscripts));
    if (manuscripts) refresh();
  }
  showInk.addEventListener("click", () => mode(true));
  showText.addEventListener("click", () => mode(false));
  document.querySelector("#refresh-manuscripts").addEventListener("click", refresh);
  document.querySelector('[data-tab-target="teacher-area"]').addEventListener("click", () => {
    if (!inbox.hidden) refresh();
  });
  if (new URLSearchParams(location.search).get("area") === "teacher") {
    document.querySelector('[data-tab-target="teacher-area"]').click();
  }
})();
