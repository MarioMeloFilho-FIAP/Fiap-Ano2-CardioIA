"""Valida a estrutura do skill_cardio.json (Fase 5 — chatbot).

Garante que o arquivo é importável no Watson e coerente com o motor local:
cada intent tem >= 5 exemplos (regra do material) e todo nó de diálogo por
intenção referencia uma intent existente.
"""

from __future__ import annotations

import json

import pytest

from chatbot import config


@pytest.fixture(scope="module")
def skill() -> dict:
    with open(config.SKILL_FILE, encoding="utf-8") as fp:
        return json.load(fp)


def test_language_pt_br(skill):
    assert skill["language"] == "pt-br"


def test_intents_tem_pelo_menos_5_exemplos(skill):
    for item in skill["intents"]:
        assert len(item["examples"]) >= 5, f"intent {item['intent']} tem poucos exemplos"


def test_intents_declaradas_batem_com_config(skill):
    intents = {i["intent"] for i in skill["intents"]}
    esperadas = config.INTENTS_DETERMINISTICOS | config.INTENTS_NLG
    assert esperadas.issubset(intents)


def test_entidades_tem_valores(skill):
    for ent in skill["entities"]:
        assert ent["values"], f"entidade {ent['entity']} sem valores"


def test_no_diagnostico_por_intent_referencia_intent_valida(skill):
    intents = {i["intent"] for i in skill["intents"]}
    for no in skill["dialog_nodes"]:
        cond = (no.get("conditions") or "").strip()
        if cond.startswith("#"):
            assert cond[1:] in intents, f"nó {no['dialog_node']} referencia intent inexistente"
