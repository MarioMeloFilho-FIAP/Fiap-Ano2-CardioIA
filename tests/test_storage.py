"""Testes da persistência SQLite (Fase 5 — chatbot)."""

from __future__ import annotations

import pytest

from chatbot.storage import ConversaStore


@pytest.fixture()
def store(tmp_path) -> ConversaStore:
    return ConversaStore(db_path=tmp_path / "teste.db")


def test_garantir_sessao_idempotente(store):
    store.garantir_sessao("s1")
    store.garantir_sessao("s1")  # não deve duplicar nem falhar
    assert store.historico("s1") == []


def test_registrar_e_recuperar_historico(store):
    store.registrar("s1", papel="usuario", texto="oi")
    store.registrar("s1", papel="assistente", texto="olá", intent="saudacao", confianca=0.9, fonte="dialogo")

    hist = store.historico("s1")
    assert len(hist) == 2
    assert hist[0]["papel"] == "usuario"
    assert hist[1]["intent"] == "saudacao"
    assert hist[1]["fonte"] == "dialogo"


def test_registrar_cria_sessao_automaticamente(store):
    store.registrar("nova", papel="usuario", texto="teste")
    assert len(store.historico("nova")) == 1


def test_sessoes_isoladas(store):
    store.registrar("a", papel="usuario", texto="msg a")
    store.registrar("b", papel="usuario", texto="msg b")
    assert len(store.historico("a")) == 1
    assert store.historico("a")[0]["texto"] == "msg a"
