"""
Projeto : CardioIA — Fase 5 (Assistente Cardiológico Conversacional)
Módulo  : Modelos de dados (dataclasses) trocados entre camadas

Tipos pequenos e imutáveis que padronizam o contrato entre o NLU (local ou
Watson), o roteador e a API Flask — evitando dicionários soltos espalhados.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Entidade:
    """Uma entidade reconhecida na mensagem (ex.: @sintoma = 'dor no peito')."""

    entidade: str
    valor: str


@dataclass(frozen=True)
class ResultadoNLU:
    """Saída padronizada do NLU, seja o motor local ou o Watson Assistant.

    ``origem`` documenta quem interpretou ('local' ou 'watson'), útil para a
    telemetria de governança.
    """

    intent: str | None
    confianca: float
    entidades: list[Entidade] = field(default_factory=list)
    origem: str = "local"

    def tem_entidade(self, entidade: str, valor: str | None = None) -> bool:
        """True se a entidade (e opcionalmente o valor) foi reconhecida."""
        return any(
            e.entidade == entidade and (valor is None or e.valor == valor)
            for e in self.entidades
        )

    def valores(self, entidade: str) -> list[str]:
        """Valores reconhecidos para uma dada entidade."""
        return [e.valor for e in self.entidades if e.entidade == entidade]


@dataclass(frozen=True)
class RespostaAssistente:
    """Resposta final entregue ao usuário, com metadados de rastreabilidade."""

    texto: str
    intent: str | None
    confianca: float
    origem_nlu: str
    fonte_resposta: str  # 'dialogo' | 'emergencia' | 'llm' | 'fallback'
    entidades: list[Entidade] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serializa para o JSON da API (/api/chat)."""
        return {
            "response": self.texto,
            "intent": self.intent,
            "confidence": round(self.confianca, 4),
            "origem_nlu": self.origem_nlu,
            "fonte_resposta": self.fonte_resposta,
            "entidades": [{"entidade": e.entidade, "valor": e.valor} for e in self.entidades],
        }
