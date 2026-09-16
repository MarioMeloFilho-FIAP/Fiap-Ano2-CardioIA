"""
Projeto : CardioIA — Fase 5 (Assistente Cardiológico Conversacional)
Módulo  : Aplicação Flask — interface web de chat + API JSON

Segue o padrão do material (Cap10, Códigos 5/6/10): rota ``/`` renderiza a
interface HTML e ``POST /api/chat`` recebe ``{"message","session_id"}`` e
devolve a resposta do assistente em JSON. A mesma API é consumida pelo app
React Native (Parte 2). CORS liberado apenas para ``/api/*``.

Aviso clínico: protótipo acadêmico de APOIO — não faz diagnóstico nem prescrição.
"""

from __future__ import annotations

import logging
import uuid

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from . import config  # importa o config já carrega o chatbot/.env
from .router import Roteador

logger = logging.getLogger(__name__)


def create_app(roteador: Roteador | None = None) -> Flask:
    """Application factory. Injeta um Roteador (facilita testes)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # mensagens de texto são pequenas
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Construção tardia: se as credenciais falharem, ainda subimos com o motor local.
    router = roteador or Roteador()

    logger.info(
        "Assistente pronto | NLU=%s | NLG=%s",
        "watson" if config.watson_habilitado() else "local",
        "on" if config.llm_habilitado() else "off",
    )

    @app.route("/")
    def index():
        return render_template(
            "chat.html",
            disclaimer=config.DISCLAIMER,
            watson_ativo=config.watson_habilitado(),
            llm_ativo=config.llm_habilitado(),
        )

    @app.get("/api/health")
    def api_health():
        return jsonify(
            status="ok",
            watson=config.watson_habilitado(),
            llm=config.llm_habilitado(),
            provider=config.LLM_PROVIDER or None,
        )

    @app.post("/api/chat")
    def api_chat():
        dados = request.get_json(silent=True) or {}
        mensagem = (dados.get("message") or "").strip()
        sessao_id = (dados.get("session_id") or "").strip() or uuid.uuid4().hex

        if not mensagem:
            return jsonify(erro="Envie o campo 'message' com a mensagem do usuário."), 400

        resposta = router.responder(mensagem, sessao_id)
        payload = resposta.to_dict()
        payload["session_id"] = sessao_id
        return jsonify(payload)

    return app


if __name__ == "__main__":
    # host=0.0.0.0 para o app mobile na mesma rede alcançar a API.
    create_app().run(host="0.0.0.0", port=config.CHATBOT_PORT, debug=True)
