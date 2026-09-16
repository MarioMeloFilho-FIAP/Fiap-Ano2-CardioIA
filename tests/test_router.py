"""Testes do roteador híbrido (Fase 5 — chatbot).

Cobrem as políticas centrais: guardrail de emergência (nunca LLM), resposta
determinística, roteamento para LLM, fallback, disclaimer e persistência.
"""

from __future__ import annotations

import pytest

from chatbot import config
from chatbot.router import Roteador
from chatbot.storage import ConversaStore


class LLMFake:
    """LLM injetável que registra se foi chamado."""

    def __init__(self):
        self.chamado = False

    def gerar(self, texto: str) -> str:
        self.chamado = True
        return "explicação gerada pelo LLM"


@pytest.fixture()
def store(tmp_path) -> ConversaStore:
    return ConversaStore(db_path=tmp_path / "router.db")


def _roteador(store, llm: object = False) -> Roteador:
    # watson/llm=False desabilitam explicitamente (independe do .env do ambiente).
    return Roteador(store=store, watson=False, llm=llm)


def test_emergencia_dispara_guardrail_sem_llm(store):
    llm = LLMFake()
    rot = _roteador(store, llm=llm)
    resp = rot.responder("acho que estou tendo um infarto", "s1")
    assert resp.fonte_resposta == "emergencia"
    assert "192" in resp.texto
    assert llm.chamado is False  # emergência NUNCA passa pelo LLM


def test_sintoma_critico_forca_emergencia(store):
    llm = LLMFake()
    rot = _roteador(store, llm=llm)
    resp = rot.responder("estou com dor no peito e falta de ar", "s1")
    assert resp.fonte_resposta == "emergencia"
    assert llm.chamado is False


def test_intent_deterministico_usa_dialogo(store):
    rot = _roteador(store)
    resp = rot.responder("quero marcar uma consulta", "s1")
    assert resp.intent == "agendar_consulta"
    assert resp.fonte_resposta == "dialogo"


def test_disclaimer_presente_em_toda_resposta(store):
    rot = _roteador(store)
    resp = rot.responder("bom dia", "s1")
    assert config.DISCLAIMER in resp.texto


def test_duvida_aberta_roteia_para_llm_quando_habilitado(store):
    llm = LLMFake()
    rot = _roteador(store, llm=llm)
    resp = rot.responder("o que e insuficiencia cardiaca", "s1")
    assert resp.fonte_resposta == "llm"
    assert llm.chamado is True


def test_duvida_clinica_roteia_para_llm_quando_habilitado(store):
    # Política ampliada: dúvidas clínicas (ex.: medicamento) também usam NLG.
    llm = LLMFake()
    rot = _roteador(store, llm=llm)
    resp = rot.responder("para que serve a losartana", "s1")
    assert resp.intent == "duvida_medicamento"
    assert resp.fonte_resposta == "llm"
    assert llm.chamado is True


def test_duvida_clinica_sem_llm_cai_no_dialogo(store):
    rot = _roteador(store)  # sem LLM
    resp = rot.responder("para que serve a losartana", "s1")
    assert resp.intent == "duvida_medicamento"
    assert resp.fonte_resposta == "dialogo"


def test_agendamento_nunca_usa_llm(store):
    # Fluxo operacional permanece determinístico mesmo com LLM disponível.
    llm = LLMFake()
    rot = _roteador(store, llm=llm)
    resp = rot.responder("quero marcar uma consulta", "s1")
    assert resp.fonte_resposta == "dialogo"
    assert llm.chamado is False


def test_duvida_aberta_sem_llm_cai_no_dialogo_ou_fallback(store):
    rot = _roteador(store)  # sem LLM
    resp = rot.responder("o que e insuficiencia cardiaca", "s1")
    assert resp.fonte_resposta in {"dialogo", "fallback"}


def test_mensagem_sem_sentido_vira_fallback(store):
    rot = _roteador(store)
    resp = rot.responder("xyzzy plugh qwerty", "s1")
    assert resp.fonte_resposta in {"fallback", "llm"}


def test_persistencia_registra_usuario_e_assistente(store):
    rot = _roteador(store)
    rot.responder("bom dia", "s1")
    hist = store.historico("s1")
    assert [m["papel"] for m in hist] == ["usuario", "assistente"]
