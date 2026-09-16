"""
Projeto : CardioIA — Fase 5 (Assistente Cardiológico Conversacional)
Módulo  : Motor NLU local

Lê o MESMO ``skill_cardio.json`` que se importa no IBM Watson Assistant (fonte
única de verdade) e faz, sem dependências pesadas:
- classificação de intenção por similaridade contra as frases-exemplo
  (no espírito dos exemplos ELIZA/Cleverbot do material didático: normalização +
  ``difflib`` + sobreposição de tokens);
- reconhecimento de entidades por sinônimos declarados no JSON (fuzzy leve);
- recuperação da resposta do nó de diálogo correspondente à intenção.

É o fallback que garante o funcionamento offline; quando há credenciais, o
``watson_client`` assume a interpretação sobre o mesmo domínio.
"""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

from . import config
from .models import Entidade, ResultadoNLU

# Palavras muito curtas/frequentes que pouco ajudam na comparação por tokens.
_STOPWORDS = {"de", "da", "do", "para", "com", "sem", "que", "meu", "minha", "no", "na", "um", "uma", "e", "ou", "a", "o", "as", "os", "em"}


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem pontuação — base para toda comparação."""
    texto = texto.lower().strip()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _tokens(texto_norm: str) -> set[str]:
    return {t for t in texto_norm.split() if len(t) > 2 and t not in _STOPWORDS}


class NLUEngine:
    """Motor NLU determinístico dirigido pelo skill JSON."""

    def __init__(self, skill_path: Path | str = config.SKILL_FILE) -> None:
        with open(skill_path, encoding="utf-8") as fp:
            self._skill = json.load(fp)
        self._intents = self._skill.get("intents", [])
        self._entities = self._skill.get("entities", [])
        self._respostas = self._mapear_respostas()

    # ------------------------------------------------------------------ setup
    def _mapear_respostas(self) -> dict[str, str]:
        """Mapeia condição do nó (ex.: '#saudacao', 'welcome') → texto."""
        mapa: dict[str, str] = {}
        for no in self._skill.get("dialog_nodes", []):
            cond = (no.get("conditions") or "").strip()
            texto = self._extrair_texto(no)
            if cond and texto:
                mapa[cond] = texto
        return mapa

    @staticmethod
    def _extrair_texto(no: dict) -> str | None:
        for item in no.get("output", {}).get("generic", []):
            valores = item.get("values", [])
            if valores and "text" in valores[0]:
                return valores[0]["text"]
        return None

    # -------------------------------------------------------------- inferência
    def interpretar(self, texto: str) -> ResultadoNLU:
        """Classifica a intenção e extrai entidades da mensagem do usuário."""
        norm = normalizar(texto)
        intent, confianca = self._classificar_intent(norm)
        entidades = self._extrair_entidades(norm)
        if confianca < config.CONFIANCA_MINIMA:
            intent = None
        return ResultadoNLU(intent=intent, confianca=confianca, entidades=entidades, origem="local")

    def _classificar_intent(self, norm: str) -> tuple[str | None, float]:
        tokens_in = _tokens(norm)
        melhor_intent: str | None = None
        melhor_score = 0.0
        for item in self._intents:
            for exemplo in item.get("examples", []):
                score = self._similaridade(norm, tokens_in, normalizar(exemplo["text"]))
                if score > melhor_score:
                    melhor_score = score
                    melhor_intent = item["intent"]
        return melhor_intent, melhor_score

    @staticmethod
    def _similaridade(norm_in: str, tokens_in: set[str], norm_ex: str) -> float:
        """Combina similaridade de sequência (difflib) e Jaccard de tokens."""
        seq = difflib.SequenceMatcher(None, norm_in, norm_ex).ratio()
        tokens_ex = _tokens(norm_ex)
        if tokens_in or tokens_ex:
            uniao = tokens_in | tokens_ex
            jaccard = len(tokens_in & tokens_ex) / len(uniao) if uniao else 0.0
        else:
            jaccard = 0.0
        return 0.5 * seq + 0.5 * jaccard

    def _extrair_entidades(self, norm: str) -> list[Entidade]:
        encontradas: list[Entidade] = []
        for ent in self._entities:
            nome = ent["entity"]
            for valor in ent.get("values", []):
                canonico = valor["value"]
                termos = [canonico, *valor.get("synonyms", [])]
                if any(self._casa_termo(norm, normalizar(t)) for t in termos):
                    encontradas.append(Entidade(entidade=nome, valor=canonico))
                    break  # um valor por entidade já basta para este protótipo
        return encontradas

    @staticmethod
    def _casa_termo(norm: str, termo_norm: str) -> bool:
        """Substring direta ou correspondência fuzzy leve (erros de digitação)."""
        if not termo_norm:
            return False
        if termo_norm in norm:
            return True
        # fuzzy só para termos de palavra única, contra cada token da entrada
        if " " not in termo_norm:
            return bool(difflib.get_close_matches(termo_norm, norm.split(), n=1, cutoff=0.85))
        return False

    # ----------------------------------------------------------------- respostas
    def resposta_dialogo(self, intent: str) -> str | None:
        """Texto do nó de diálogo cuja condição é '#<intent>'."""
        return self._respostas.get(f"#{intent}")

    def resposta_welcome(self) -> str:
        return self._respostas.get("welcome", "Olá! Como posso ajudar?")

    def resposta_fallback(self) -> str:
        return self._respostas.get("anything_else", config.RESPOSTA_FALLBACK)
