"""Testes do motor NLU local (Fase 5 — chatbot). Não dependem de TensorFlow."""

from __future__ import annotations

import pytest

from chatbot.engine import NLUEngine, normalizar


@pytest.fixture(scope="module")
def engine() -> NLUEngine:
    return NLUEngine()


def test_normalizar_remove_acentos_e_pontuacao():
    assert normalizar("Olá, coração!") == "ola coracao"


@pytest.mark.parametrize(
    "texto, intent_esperado",
    [
        ("oi, bom dia", "saudacao"),
        ("quero marcar uma consulta", "agendar_consulta"),
        ("quando sai o resultado do meu exame", "resultado_exame"),
        ("quais alimentos sao bons para o coracao", "habitos_saudaveis"),
        ("para que serve a losartana", "duvida_medicamento"),
    ],
)
def test_classifica_intents_principais(engine, texto, intent_esperado):
    resultado = engine.interpretar(texto)
    assert resultado.intent == intent_esperado
    assert resultado.confianca > 0


def test_extrai_entidade_sintoma_por_sinonimo(engine):
    resultado = engine.interpretar("estou com aperto no peito")
    assert resultado.tem_entidade("sintoma", "dor no peito")


def test_extrai_entidade_medicamento(engine):
    resultado = engine.interpretar("posso tomar losartan a noite")
    assert "losartana" in resultado.valores("medicamento")


def test_baixa_confianca_vira_intent_none(engine):
    # Texto sem relação com o domínio → confiança baixa → intent None.
    resultado = engine.interpretar("xyzzy plugh qwerty")
    assert resultado.intent is None


def test_resposta_dialogo_existe_para_intent(engine):
    assert engine.resposta_dialogo("saudacao")
    assert engine.resposta_fallback()
