"""
Projeto : CardioIA — Fase 5 (Assistente Cardiológico Conversacional)
Módulo  : Persistência em SQLite (sessões + mensagens)

Guarda o histórico da conversa para rastreabilidade/telemetria (governança,
Cap07). Usa apenas a stdlib (``sqlite3``). Governança de dados: armazenamos o
mínimo necessário (texto trocado + metadados de NLU); não coletamos dados
identificáveis do paciente por conta própria.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessoes (
    id          TEXT PRIMARY KEY,
    inicio      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mensagens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sessao_id   TEXT NOT NULL,
    papel       TEXT NOT NULL,          -- 'usuario' | 'assistente'
    texto       TEXT NOT NULL,
    intent      TEXT,
    confianca   REAL,
    fonte       TEXT,                   -- 'dialogo' | 'emergencia' | 'llm' | 'fallback'
    ts          TEXT NOT NULL,
    FOREIGN KEY (sessao_id) REFERENCES sessoes(id)
);
"""


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversaStore:
    """Camada fina de acesso ao SQLite do assistente."""

    def __init__(self, db_path: Path | str = config.DB_PATH) -> None:
        self.db_path = str(db_path)
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    # ------------------------------------------------------------------ sessão
    def garantir_sessao(self, sessao_id: str) -> None:
        """Cria a sessão se ainda não existir (idempotente)."""
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sessoes (id, inicio) VALUES (?, ?)",
                (sessao_id, _agora()),
            )

    # --------------------------------------------------------------- mensagens
    def registrar(
        self,
        sessao_id: str,
        papel: str,
        texto: str,
        intent: str | None = None,
        confianca: float | None = None,
        fonte: str | None = None,
    ) -> None:
        """Grava uma mensagem (do usuário ou do assistente)."""
        self.garantir_sessao(sessao_id)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO mensagens (sessao_id, papel, texto, intent, confianca, fonte, ts)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sessao_id, papel, texto, intent, confianca, fonte, _agora()),
            )

    def historico(self, sessao_id: str) -> list[dict]:
        """Mensagens de uma sessão em ordem cronológica."""
        with self._conn() as conn:
            linhas = conn.execute(
                "SELECT papel, texto, intent, confianca, fonte, ts FROM mensagens"
                " WHERE sessao_id = ? ORDER BY id",
                (sessao_id,),
            ).fetchall()
        return [dict(l) for l in linhas]
