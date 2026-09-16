"""
Projeto : CardioIA — Fase 5 (Assistente Cardiológico Conversacional)
Módulo  : Integração com IBM Watson Assistant (AssistantV2)

Ativado apenas quando há credenciais (WA_API_KEY / WA_URL / WA_ASSISTANT_ID).
Segue o padrão do material didático (Cap10, Código 10): cria uma sessão, envia a
mensagem e traduz a resposta do Watson para o mesmo ``ResultadoNLU`` que o motor
local produz — assim o roteador não precisa saber quem interpretou.

O SDK ``ibm-watson`` é importado de forma tardia: sua ausência não quebra o app
(o roteador cai no motor local). Instale-o só se for usar o Watson de verdade.
"""

from __future__ import annotations

from . import config
from .models import Entidade, ResultadoNLU


class WatsonIndisponivelError(RuntimeError):
    """Sinaliza que o Watson não pôde ser usado (sem SDK, credencial ou rede)."""


class WatsonNLU:
    """Interpreta mensagens via IBM Watson Assistant, quando configurado."""

    def __init__(self) -> None:
        if not config.watson_habilitado():
            raise WatsonIndisponivelError("Credenciais do Watson ausentes.")
        try:
            from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
            from ibm_watson import AssistantV2
        except ImportError as exc:  # SDK não instalado
            raise WatsonIndisponivelError(
                "SDK 'ibm-watson' não instalado. Rode: uv pip install ibm-watson"
            ) from exc

        authenticator = IAMAuthenticator(config.WA_API_KEY)
        self._assistant = AssistantV2(version=config.WA_VERSION, authenticator=authenticator)
        self._assistant.set_service_url(config.WA_URL)
        self._assistant_id = config.WA_ASSISTANT_ID
        # Cache de sessão por session_id do nosso app (Watson tem seu próprio id).
        self._sessoes: dict[str, str] = {}

    def _sessao_watson(self, sessao_id: str) -> str:
        if sessao_id not in self._sessoes:
            resp = self._assistant.create_session(assistant_id=self._assistant_id).get_result()
            self._sessoes[sessao_id] = resp["session_id"]
        return self._sessoes[sessao_id]

    def interpretar(self, texto: str, sessao_id: str) -> tuple[ResultadoNLU, str | None]:
        """Envia a mensagem ao Watson e devolve (ResultadoNLU, texto_resposta).

        O Watson já retorna a resposta do diálogo em ``output.generic``; nós a
        aproveitamos quando presente, mantendo o fluxo de negócio no serviço.
        """
        try:
            wa_session = self._sessao_watson(sessao_id)
            resp = self._assistant.message(
                assistant_id=self._assistant_id,
                session_id=wa_session,
                input={"message_type": "text", "text": texto},
            ).get_result()
        except Exception as exc:  # rede/serviço indisponível → deixa o router decidir
            raise WatsonIndisponivelError(str(exc)) from exc

        output = resp.get("output", {})
        intents = output.get("intents", [])
        intent = intents[0]["intent"] if intents else None
        confianca = float(intents[0]["confidence"]) if intents else 0.0
        entidades = [
            Entidade(entidade=e["entity"], valor=e.get("value", "")) for e in output.get("entities", [])
        ]
        texto_resposta = None
        for item in output.get("generic", []):
            if item.get("response_type") == "text" and item.get("text"):
                texto_resposta = item["text"]
                break

        resultado = ResultadoNLU(
            intent=intent, confianca=confianca, entidades=entidades, origem="watson"
        )
        return resultado, texto_resposta
