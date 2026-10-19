/* Institutional teacher decisions. Every write is authenticated and persisted by the API. */
(function teacherDecisions() {
  "use strict";
  const labels = Object.freeze({ SUBMITTED: "Enviada", TRANSCRIPTION_REVIEW: "Transcrição em conferência",
    ANALYSIS_AVAILABLE: "Análise disponível", DECISION_DRAFT: "Decisão em rascunho",
    DECISION_FINALIZED: "Decisão finalizada", RESULT_RELEASED: "Resultado liberado" });
  const decisionLabel = decision => ({ DRAFT: labels.DECISION_DRAFT, FINALIZED: labels.DECISION_FINALIZED,
    RELEASED: labels.RESULT_RELEASED })[decision?.status] || "Sem decisão";
  const points = value => Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 2 });
  const node = (tag, text) => { const element = document.createElement(tag); if (text !== undefined) element.textContent = text; return element; };
  async function request(url, method = "GET", body) {
    let response, data;
    try {
      response = await fetch(url, { method, credentials: "same-origin", cache: "no-store",
        ...(body === undefined ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }) });
      data = await response.json();
    } catch (error) {
      console.error("ConfIA: transporte da decisão", error);
      throw new Error("Não foi possível comunicar com o servidor. Tente novamente.");
    }
    if (!response.ok) {
      console.error("ConfIA: decisão", response.status, data);
      const error = new Error(response.status === 409
        ? "A decisão pode ter sido alterada em outra sessão ou a análise está desatualizada. Recarregue a decisão para continuar."
        : response.status === 422 ? "Confira a pontuação, o feedback e a justificativa da alteração."
          : "Não foi possível concluir a ação. Tente novamente.");
      error.status = response.status;
      throw error;
    }
    return data;
  }
  function mount(panel, record, onChange = () => {}) {
    let decision = null, openedRun = null, openedUsable = false, busy = false, dirty = false, loaded = false;
    let fields = {}, status, sourceMessage, useRun, useSuggestion, overrideLabel;
    const controller = { get busy() { return busy; }, get decision() { return decision; }, isDirty: () => dirty,
      setOpenedRun(run, usable) { openedRun = run; openedUsable = usable; updateSource(); } };
    panel.className = "teacher-decision-panel";
    panel.setAttribute("aria-label", "Decisão do professor");
    function button(label, action, host = panel, primary = false) {
      const element = node("button", label); element.type = "button"; element.className = primary ? "primary-action" : "secondary-action";
      element.addEventListener("click", action); host.appendChild(element); return element;
    }
    function control(label, key, tag = "textarea", host = panel) {
      const wrapper = node("label"); wrapper.appendChild(node("span", label));
      wrapper.className = "form-field";
      const input = node(tag); input.value = decision[key] == null ? "" : key === "teacher_final_points" ? String(decision[key]).replace(".", ",") : String(decision[key]);
      input.name = key;
      input.maxLength = key === "override_reason" ? 2000 : key === "teacher_final_points" ? 12 : 10000;
      input.setAttribute("aria-describedby", status.id);
      input.addEventListener("input", () => { input.setAttribute("aria-invalid", "false"); dirty = true; updateOverride(); });
      wrapper.appendChild(input); host.appendChild(wrapper); fields[key] = input;
      return wrapper;
    }
    function updateOverride() {
      if (!overrideLabel) return;
      const final = fields.teacher_final_points.value.trim().replace(",", ".");
      const override = decision.confia_suggested_points != null && final !== ""
        && Number(final) !== Number(decision.confia_suggested_points);
      overrideLabel.hidden = !override;
      fields.override_reason.required = override;
    }
    function updateSource() {
      if (!sourceMessage) return;
      const current = openedRun && openedUsable;
      sourceMessage.textContent = openedRun ? current
        ? `Análise aberta: revisão ${openedRun.revision_number} · ${new Date(openedRun.created_at).toLocaleString("pt-BR")}`
        : "A análise aberta está desatualizada ou indisponível. Abra uma análise atual ou decida manualmente."
        : "Sem análise aberta. Você pode registrar uma decisão manual.";
      if (useRun) useRun.disabled = busy || !current;
    }
    function setBusy(value) {
      busy = value;
      for (const control of panel.querySelectorAll("button, input, textarea")) control.disabled = value;
      if (useSuggestion) useSuggestion.disabled = value || decision?.audit_state !== "current";
      panel.setAttribute("aria-busy", String(value));
      updateSource();
    }
    function values() {
      const raw = fields.teacher_final_points.value.trim().replace(",", ".");
      if (raw !== "" && (!/^\d+(?:\.\d{1,2})?$/.test(raw) || Number(raw) > Number(decision.item_max_points))) {
        fields.teacher_final_points.setAttribute("aria-invalid", "true");
        throw new Error(`Informe uma pontuação entre 0 e ${points(decision.item_max_points)}, com até duas casas decimais.`);
      }
      return { teacher_final_points: raw || null, teacher_feedback: fields.teacher_feedback.value,
        teacher_internal_note: fields.teacher_internal_note.value || null, override_reason: fields.override_reason.value || null };
    }
    function accept(value) { decision = value; dirty = false; onChange(value); }
    async function act(operation, success) {
      if (busy) return;
      setBusy(true);
      status.textContent = "Salvando decisão…"; status.dataset.kind = "info";
      try { await operation(); render(); status.textContent = success; status.dataset.kind = "success"; }
      catch (error) { status.textContent = error.status === 403 ? "Seu vínculo docente não autoriza esta decisão." : error.message; status.dataset.kind = "error"; }
      finally {
        setBusy(false);
        Object.values(fields).find(field => field.getAttribute("aria-invalid") === "true")?.focus();
      }
    }
    async function save(extra = {}) {
      accept(await request(`/teacher-decisions/${decision.decision_id}`, "PATCH",
        { ...values(), ...extra, expected_version: decision.version }));
    }
    function render() {
      panel.replaceChildren(node("h3", "Decisão do professor"));
      fields = {}; useRun = null; useSuggestion = null; overrideLabel = null; sourceMessage = null;
      const badge = node("p", decision ? decisionLabel(decision) : "Nenhuma decisão registrada.");
      badge.className = "status";
      badge.dataset.kind = decision?.status === "RELEASED" ? "success" : decision?.status === "DRAFT" ? "pending" : "info";
      panel.appendChild(badge);
      status = node("p"); status.className = "action-message";
      status.id = `decision-message-${record.submission_id}`;
      status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite"); panel.appendChild(status);
      if (!record.assessment_id) {
        badge.hidden = true;
        status.textContent = "Envio anterior sem avaliação vinculada. Decisão institucional indisponível."; return;
      }
      if (!loaded) {
        badge.hidden = true;
        status.textContent = "Carregando decisão…";
        button("Recarregar decisão", load); return;
      }
      if (decision && decision.status !== "DRAFT") {
        const score = node("p", `Pontuação final do professor: ${points(decision.teacher_final_points)} / ${points(decision.item_max_points)}`);
        score.className = "decision-final-score"; panel.appendChild(score);
        const feedback = node("section"); feedback.className = "decision-feedback";
        feedback.appendChild(node("h4", "Feedback ao aluno"));
        feedback.appendChild(node("p", decision.teacher_feedback || "Nenhum feedback registrado.")); panel.appendChild(feedback);
        if (decision.status === "FINALIZED") {
          const actions = node("div"); actions.className = "action-row"; panel.appendChild(actions);
          button("Liberar resultado ao aluno", () => act(async () => {
            accept(await request(`/teacher-decisions/${decision.decision_id}/release`, "POST"));
          }, "Resultado liberado ao aluno"), actions, true);
        }
        const privateDetails = node("details"); privateDetails.appendChild(node("summary", "Registro interno da decisão"));
        if (decision.confia_suggested_points != null) privateDetails.appendChild(node("p", `Pontuação sugerida pelo ConfIA: ${points(decision.confia_suggested_points)} / ${points(decision.item_max_points)}`));
        privateDetails.appendChild(node("p", `Nota interna: ${decision.teacher_internal_note || "—"}`));
        privateDetails.appendChild(node("p", `Justificativa da alteração: ${decision.override_reason || "—"}`));
        privateDetails.appendChild(node("p", `Análise vinculada: ${decision.audit_run_id || "Decisão manual"}`));
        panel.appendChild(privateDetails);
        return;
      }
      sourceMessage = node("p"); sourceMessage.className = "form-help";
      if (!decision) {
        panel.appendChild(sourceMessage);
        const actions = node("div"); actions.className = "action-row"; panel.appendChild(actions);
        useRun = button("Iniciar decisão com análise aberta", () => act(async () => {
          accept(await request(`/submissions/${record.submission_id}/teacher-decision`, "POST", { audit_run_id: openedRun.audit_run_id }));
        }, "Rascunho criado. Preencha a pontuação final e o feedback."), actions, true);
        button("Iniciar decisão manual", () => act(async () => {
          accept(await request(`/submissions/${record.submission_id}/teacher-decision`, "POST", {}));
        }, "Rascunho manual criado."), actions);
        updateSource(); return;
      }
      const scoring = node("div"); scoring.className = "decision-scoring"; panel.appendChild(scoring);
      if (decision.confia_suggested_points != null) {
        const suggestion = node("p", `Pontuação sugerida pelo ConfIA: ${points(decision.confia_suggested_points)} / ${points(decision.item_max_points)}`);
        suggestion.className = "decision-suggestion"; scoring.appendChild(suggestion);
      } else scoring.appendChild(node("p", "Sem pontuação sugerida. Informe a pontuação final do professor.")).className = "form-help";
      const finalField = control("Pontuação final", "teacher_final_points", "input", scoring);
      finalField.className = "form-field decision-final-field";
      finalField.appendChild(node("span", `/ ${points(decision.item_max_points)}`)).className = "decision-maximum";
      fields.teacher_final_points.type = "text"; fields.teacher_final_points.inputMode = "decimal";
      if (decision.confia_suggested_points != null) {
        useSuggestion = button("Usar sugestão", () => {
          fields.teacher_final_points.value = String(decision.confia_suggested_points).replace(".", ",");
          fields.teacher_final_points.setAttribute("aria-invalid", "false"); dirty = true; updateOverride();
          status.textContent = "Sugestão copiada. Confira o feedback e salve ou finalize a decisão."; status.dataset.kind = "info";
        }, scoring);
        useSuggestion.disabled = decision.audit_state !== "current";
      }
      const feedback = node("div"); feedback.className = "decision-feedback"; panel.appendChild(feedback);
      control("Feedback ao aluno", "teacher_feedback", "textarea", feedback);
      feedback.appendChild(node("p", "O aluno verá este feedback quando o resultado for liberado.")).className = "form-help";
      const internal = node("section"); internal.className = "decision-internal-fields"; panel.appendChild(internal);
      internal.appendChild(node("h4", "Registro interno · somente professor"));
      control("Nota interna (somente professor)", "teacher_internal_note", "textarea", internal);
      overrideLabel = control("Justificativa da alteração (somente professor)", "override_reason", "textarea", internal);
      const actions = node("div"); actions.className = "action-row decision-actions"; panel.appendChild(actions);
      button("Salvar rascunho", () => act(() => save(), "Rascunho salvo."), actions);
      button("Finalizar decisão", () => act(async () => {
        const current = values();
        if (current.teacher_final_points === null) {
          fields.teacher_final_points.setAttribute("aria-invalid", "true");
          throw new Error("Informe a pontuação final do professor.");
        }
        if (decision.confia_suggested_points != null && Number(current.teacher_final_points) !== Number(decision.confia_suggested_points)
            && !(current.override_reason || "").trim()) {
          fields.override_reason.setAttribute("aria-invalid", "true");
          throw new Error("Justifique a alteração da pontuação sugerida antes de finalizar.");
        }
        if (dirty) await save();
        accept(await request(`/teacher-decisions/${decision.decision_id}/finalize`, "POST", { expected_version: decision.version }));
      }, "Decisão finalizada"), actions, true);
      const auxiliary = node("div"); auxiliary.className = "action-row decision-auxiliary"; panel.appendChild(auxiliary);
      button("Descartar alterações da decisão", () => { dirty = false; render(); status.textContent = "Alterações descartadas."; }, auxiliary);
      button("Recarregar decisão salva", () => { if (!dirty) load(); else status.textContent = "Salve ou descarte as alterações antes de recarregar."; }, auxiliary);
      const provenance = node("details"); provenance.className = "decision-analysis-source";
      provenance.appendChild(node("summary", "Análise vinculada à decisão"));
      provenance.appendChild(sourceMessage);
      if (["stale", "unavailable"].includes(decision.audit_state)) {
        const warning = node("p", "A análise vinculada está desatualizada ou indisponível. Vincule uma análise atual ou escolha decisão manual antes de finalizar.");
        warning.className = "alert"; warning.dataset.kind = "warning";
        panel.appendChild(warning);
      }
      provenance.appendChild(node("p", decision.audit_run_id || "Decisão manual, sem sugestão ConfIA."));
      if (decision.audit_run_id) provenance.appendChild(node("p", `Escala original: ${decision.confia_score_raw ?? "—"} / ${decision.confia_max_score_raw ?? "—"}`));
      const linkage = node("div"); linkage.className = "action-row"; provenance.appendChild(linkage);
      useRun = button("Vincular análise aberta", () => act(() => save({ audit_run_id: openedRun.audit_run_id }), "Análise vinculada ao rascunho."), linkage);
      if (decision.audit_run_id) button("Decidir sem sugestão ConfIA", () => act(() => save({ audit_run_id: null }), "Rascunho manual salvo."), linkage);
      panel.appendChild(provenance);
      updateOverride(); updateSource();
    }
    async function load() {
      if (busy) return;
      setBusy(true);
      try {
        accept(await request(`/submissions/${record.submission_id}/teacher-decision`));
        loaded = true; render();
      } catch (_) { status.textContent = "Não foi possível carregar a decisão. Recarregue para continuar."; }
      finally { setBusy(false); }
    }
    render();
    if (record.assessment_id) load();
    return controller;
  }
  window.ConfIADecisions = { mount, labels, decisionLabel };
})();
