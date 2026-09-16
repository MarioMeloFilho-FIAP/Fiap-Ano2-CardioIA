/* CardioIA — Fase 5: cliente do chat (fetch para POST /api/chat).
 * Sessão gerada no cliente e mantida na aba (sessionStorage) para agrupar as
 * mensagens no backend (SQLite). Vanilla JS, no espírito do Código 6 do material.
 */
(function () {
  "use strict";

  const $mensagens = document.getElementById("mensagens");
  const $form = document.getElementById("form");
  const $campo = document.getElementById("campo");
  const $botao = $form.querySelector("button");

  // Um id de sessão por aba do navegador.
  let sessionId = sessionStorage.getItem("cardioia_session");
  if (!sessionId) {
    sessionId = (crypto.randomUUID && crypto.randomUUID()) ||
      String(Date.now()) + Math.random().toString(16).slice(2);
    sessionStorage.setItem("cardioia_session", sessionId);
  }

  function adicionarBolha(texto, papel, opcoes) {
    const div = document.createElement("div");
    div.className = "bolha " + papel + (opcoes && opcoes.emergencia ? " emergencia" : "");
    div.textContent = texto;
    if (opcoes && opcoes.meta) {
      const meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = opcoes.meta;
      div.appendChild(meta);
    }
    $mensagens.appendChild(div);
    // Rola no próximo frame: garante que a altura já foi recalculada (texto longo).
    requestAnimationFrame(function () {
      $mensagens.scrollTop = $mensagens.scrollHeight;
    });
    return div;
  }

  // Mensagem de boas-vindas.
  adicionarBolha(
    "Olá! Sou o assistente virtual do CardioIA. Posso orientar sobre sintomas, " +
      "consultas, exames, medicamentos e hábitos saudáveis. Como posso ajudar?",
    "assistente"
  );

  async function enviar(mensagem) {
    adicionarBolha(mensagem, "usuario");
    $botao.disabled = true;
    const pensando = adicionarBolha("digitando…", "assistente");

    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: mensagem, session_id: sessionId }),
      });
      const dados = await resp.json();
      pensando.remove();

      if (!resp.ok) {
        adicionarBolha(dados.erro || "Erro ao contatar o assistente.", "assistente");
        return;
      }
      const fontes = {
        dialogo: "NLU",
        emergencia: "emergência",
        llm: "NLG",
        fallback: "esclarecimento",
      };
      const fonte = fontes[dados.fonte_resposta] || dados.fonte_resposta;
      const base = dados.intent
        ? "intenção: " + dados.intent + " · " + Math.round((dados.confidence || 0) * 100) + "%"
        : "não reconhecida";
      const meta = base + " · " + fonte;
      adicionarBolha(dados.response, "assistente", {
        meta: meta,
        emergencia: dados.fonte_resposta === "emergencia",
      });
    } catch (e) {
      pensando.remove();
      adicionarBolha("Falha de rede. Verifique se o backend está no ar.", "assistente");
    } finally {
      $botao.disabled = false;
      $campo.focus();
    }
  }

  $form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    const texto = $campo.value.trim();
    if (!texto) return;
    $campo.value = "";
    enviar(texto);
  });
})();
