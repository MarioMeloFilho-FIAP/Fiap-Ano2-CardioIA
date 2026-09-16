"""
Projeto : CardioIA — Fase 5 (Assistente Cardiológico Conversacional)
Módulo  : Roteador / orquestrador da conversa

Implementa a arquitetura HÍBRIDA NLU+NLG do material (Cap10, Código 10):

    mensagem
      │
      ├─ NLU (Watson se houver credenciais; senão motor local)
      │
      ├─ 1) GUARDRAIL de emergência  → resposta fixa SAMU 192 (nunca LLM)
      ├─ 2) intent determinístico    → resposta do diálogo (skill_cardio.json)
      ├─ 3) dúvida aberta / baixa conf. + LLM habilitado → geração NLG
      └─ 4) fallback                 → pedido de esclarecimento

Toda resposta recebe o disclaimer clínico e é persistida (rastreabilidade).
"""

from __future__ import annotations

import logging

from . import config
from .engine import NLUEngine
from .models import RespostaAssistente, ResultadoNLU
from .storage import ConversaStore

logger = logging.getLogger(__name__)


class Roteador:
    """Decide a resposta do assistente a partir do NLU e das políticas."""

    def __init__(
        self,
        engine: NLUEngine | None = None,
        store: ConversaStore | None = None,
        watson=None,
        llm=None,
    ) -> None:
        # `watson`/`llm` podem ser injetados (testes); senão, construídos por env.
        self._engine = engine or NLUEngine()
        self._store = store or ConversaStore()
        self._watson = watson if watson is not None else self._maybe_watson()
        self._llm = llm if llm is not None else self._maybe_llm()

    @staticmethod
    def _maybe_watson():
        if not config.watson_habilitado():
            return None
        try:
            from .watson_client import WatsonNLU

            return WatsonNLU()
        except Exception:  # SDK/credencial/rede — segue com o motor local
            return None

    @staticmethod
    def _maybe_llm():
        if not config.llm_habilitado():
            logger.info("NLG desabilitado (sem provedor/chave de LLM). Usando só NLU.")
            return None
        try:
            from .llm_client import LLMClient

            cliente = LLMClient()
            logger.info("NLG habilitado (provedor=%s).", config.LLM_PROVIDER)
            return cliente
        except Exception as exc:
            logger.warning("NLG indisponível: %s", exc)
            return None

    # ------------------------------------------------------------------ público
    def responder(self, texto: str, sessao_id: str) -> RespostaAssistente:
        """Fluxo completo para uma mensagem do usuário."""
        self._store.registrar(sessao_id, papel="usuario", texto=texto)

        nlu, resposta_watson = self._interpretar(texto, sessao_id)
        resposta = self._decidir(texto, nlu, resposta_watson)

        self._store.registrar(
            sessao_id,
            papel="assistente",
            texto=resposta.texto,
            intent=resposta.intent,
            confianca=resposta.confianca,
            fonte=resposta.fonte_resposta,
        )
        return resposta

    # ------------------------------------------------------------------ interno
    def _interpretar(self, texto: str, sessao_id: str) -> tuple[ResultadoNLU, str | None]:
        """Usa o Watson quando disponível; caso contrário, o motor local."""
        if self._watson:
            try:
                return self._watson.interpretar(texto, sessao_id)
            except Exception:
                pass  # degrada para o motor local
        return self._engine.interpretar(texto), None

    def _decidir(
        self, texto: str, nlu: ResultadoNLU, resposta_watson: str | None
    ) -> RespostaAssistente:
        # 1) Guardrail de emergência — tem prioridade máxima e nunca usa LLM.
        if self._eh_emergencia(nlu):
            return self._montar(config.RESPOSTA_EMERGENCIA, nlu, "emergencia")

        # 2) Intent de fluxo determinístico → resposta do diálogo (nunca NLG).
        if nlu.intent in config.INTENTS_DETERMINISTICOS:
            texto_resp = resposta_watson or self._engine.resposta_dialogo(nlu.intent)
            if texto_resp:
                return self._montar(texto_resp, nlu, "dialogo")

        # 3) Intent elegível a NLG (dúvida clínica/aberta) ou não reconhecido,
        #    com LLM habilitado → geração.
        if self._elegivel_llm(nlu) and self._llm:
            try:
                return self._montar(self._llm.gerar(texto), nlu, "llm")
            except Exception as exc:
                logger.warning("Falha na geração NLG, usando resposta determinística: %s", exc)

        # 3b) Sem LLM (ou falha): se o intent tem nó de diálogo, usa-o.
        if nlu.intent:
            texto_resp = resposta_watson or self._engine.resposta_dialogo(nlu.intent)
            if texto_resp:
                return self._montar(texto_resp, nlu, "dialogo")

        # 4) Fallback / esclarecimento.
        return self._montar(self._engine.resposta_fallback(), nlu, "fallback")

    @staticmethod
    def _eh_emergencia(nlu: ResultadoNLU) -> bool:
        if nlu.intent == "emergencia":
            return True
        # Sintoma crítico reconhecido dispara o guardrail mesmo com outra intent.
        return any(v in config.SINTOMAS_CRITICOS for v in nlu.valores("sintoma"))

    @staticmethod
    def _elegivel_llm(nlu: ResultadoNLU) -> bool:
        return nlu.intent in config.INTENTS_NLG or nlu.intent is None

    @staticmethod
    def _montar(texto: str, nlu: ResultadoNLU, fonte: str) -> RespostaAssistente:
        return RespostaAssistente(
            texto=f"{texto}\n\n{config.DISCLAIMER}",
            intent=nlu.intent,
            confianca=nlu.confianca,
            origem_nlu=nlu.origem,
            fonte_resposta=fonte,
            entidades=list(nlu.entidades),
        )
