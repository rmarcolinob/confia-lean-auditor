(function expose(root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.ConfiaSubmissionClient = api;
})(globalThis, function submissionClient() {
  "use strict";
  const MAX_SNAPSHOT_BYTES = 10 * 1024 * 1024;
  const MAX_PNG_BYTES = 8 * 1024 * 1024;

  async function base64(blob) {
    const bytes = new Uint8Array(await blob.arrayBuffer());
    let binary = "";
    for (let i = 0; i < bytes.length; i += 8192) {
      binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
    }
    return btoa(binary);
  }

  function validReceipt(receipt, snapshot) {
    const hash = (value) => typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
    return receipt && /^sub_[0-9a-f]{32}$/.test(receipt.submission_id)
      && receipt.status === "RECEIVED" && receipt.source === "tablet"
      && receipt.receipt_version === "1.0" && receipt.capture_schema_version === snapshot.schema_version
      && receipt.snapshot_id === snapshot.local_snapshot_id && receipt.problem_id === snapshot.problem_id
      && typeof receipt.received_at === "string" && Number.isFinite(Date.parse(receipt.received_at))
      && hash(receipt.snapshot?.sha256) && Array.isArray(receipt.page_images)
      && receipt.page_images.length === snapshot.pages.length
      && snapshot.pages.every((page) => receipt.page_images.some((ref) =>
        ref.page_id === page.page_id && ref.page_index === page.index && hash(ref.sha256)));
  }

  function create(canvas, transport) {
    let prepared = null;
    let inFlight = false;
    async function send(document, target = "/submissions") {
      if (document?.document_kind !== "local_snapshot" || !document.local_snapshot_id) {
        throw new Error("Prepare uma versão congelada antes de enviar.");
      }
      if (inFlight) throw new Error("Aguarde o envio em andamento.");
      if (target !== "/submissions" && !/^\/assessments\/asmt_[0-9a-f]{32}\/items\/ait_[0-9a-f]{32}\/submissions$/.test(target)) {
        throw new Error("Destino do envio inválido.");
      }
      inFlight = true;
      try {
        // Own immutable copy; neither PNG creation nor retries touch the open draft.
        const snapshotJson = JSON.stringify(document, null, 2);
        const snapshot = JSON.parse(snapshotJson);
        if (new TextEncoder().encode(snapshotJson).length > MAX_SNAPSHOT_BYTES) {
          throw new Error("Snapshot acima do limite de 10 MiB. Preserve a exportação local.");
        }
        if (!prepared || prepared.source !== snapshotJson) {
          const pages = [];
          for (const page of [...snapshot.pages].sort((a, b) => a.index - b.index)) {
            const blob = await canvas.pngBlob(snapshot, page.page_id);
            if (blob.size > MAX_PNG_BYTES) throw new Error("PNG acima do limite de 8 MiB por página.");
            pages.push({ page_id: page.page_id, png_base64: await base64(blob) });
          }
          // Cache exact bytes, including every PNG, for a retry after a lost response.
          prepared = { source: snapshotJson, body: JSON.stringify({ snapshot_json: snapshotJson, pages }) };
        }
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 30000);
        let response;
        let receipt;
        try {
          response = await transport(target, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: prepared.body, signal: controller.signal, cache: "no-store",
          });
          if (response.ok) {
            try { receipt = await response.json(); } catch (_) { /* Missing receipt is not success. */ }
          }
        } catch (_) {
          throw new Error("Sem confirmação do servidor. Sua versão local foi preservada; tente enviar novamente.");
        } finally {
          clearTimeout(timer);
        }
        if (!response.ok) {
          const message = response.status === 409
            ? "Conflito: esta versão já existe com conteúdo diferente. Preserve os artefatos locais e peça revisão técnica."
            : `Servidor não confirmou o recebimento (HTTP ${response.status}). Preserve a cópia local e tente novamente.`;
          throw new Error(message);
        }
        if (![200, 201].includes(response.status) || !validReceipt(receipt, snapshot)) {
          throw new Error("Resposta sem recibo válido. A versão local foi preservada; tente novamente.");
        }
        if (target !== "/submissions") {
          const [, , assessmentId, , itemId] = target.split("/");
          if (receipt.assessment_id !== assessmentId || receipt.assessment_item_id !== itemId) {
            throw new Error("Recibo não corresponde à questão do exame. Preserve a versão local.");
          }
        }
        return receipt;
      } finally {
        inFlight = false;
      }
    }
    return { send };
  }
  return { create, validReceipt };
});
