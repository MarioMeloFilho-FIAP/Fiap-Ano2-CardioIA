"""
Projeto : CardioIA — Fase 5 (Assistente Cardiológico Conversacional)
Módulo  : Camada NLG (LLM) — NEUTRA de provedor

Segue o material didático (Cap10, Códigos 7/8/9): a mesma aplicação troca de
provedor (OpenAI / Anthropic / Gemini) sem mudar a lógica de negócio. É opcional
e ativada por variável de ambiente — a ausência do SDK ou da chave NÃO quebra o
app (o roteador cai na resposta determinística).

Governança: envia sempre o system prompt clínico (sem diagnóstico/prescrição) e
NUNCA recebe as chaves de API em código — apenas de ``os.environ`` via config.
"""

from __future__ import annotations

from . import config

# Modelos padrão por provedor (sobrescrevíveis por LLM_MODEL no .env).
_MODELOS_PADRAO = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-latest",
    "gemini": "gemini-1.5-flash",
}

_MAX_TOKENS = 400


class LLMIndisponivelError(RuntimeError):
    """Sinaliza que a geração por LLM não pôde ser realizada."""


class LLMClient:
    """Gera respostas em linguagem natural pelo provedor configurado."""

    def __init__(self) -> None:
        if not config.llm_habilitado():
            raise LLMIndisponivelError("Nenhum provedor de LLM configurado (sem chave de API).")
        self.provider = config.LLM_PROVIDER
        self.modelo = config.LLM_MODEL or _MODELOS_PADRAO.get(self.provider, "")

    def gerar(self, mensagem: str) -> str:
        """Roteia para o provedor certo; devolve o texto gerado."""
        try:
            if self.provider == "openai":
                return self._gerar_openai(mensagem)
            if self.provider == "anthropic":
                return self._gerar_anthropic(mensagem)
            if self.provider == "gemini":
                return self._gerar_gemini(mensagem)
        except LLMIndisponivelError:
            raise
        except Exception as exc:  # falha de SDK/rede → roteador usa fallback
            raise LLMIndisponivelError(f"Falha ao gerar com {self.provider}: {exc}") from exc
        raise LLMIndisponivelError(f"Provedor de LLM desconhecido: {self.provider}")

    # ------------------------------------------------------------- provedores
    def _gerar_openai(self, mensagem: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMIndisponivelError("SDK 'openai' não instalado.") from exc
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=self.modelo,
            max_tokens=_MAX_TOKENS,
            messages=[
                {"role": "system", "content": config.SYSTEM_PROMPT_CLINICO},
                {"role": "user", "content": mensagem},
            ],
        )
        return (resp.choices[0].message.content or "").strip()

    def _gerar_anthropic(self, mensagem: str) -> str:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise LLMIndisponivelError("SDK 'anthropic' não instalado.") from exc
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=self.modelo,
            max_tokens=_MAX_TOKENS,
            system=config.SYSTEM_PROMPT_CLINICO,
            messages=[{"role": "user", "content": mensagem}],
        )
        return "".join(bloco.text for bloco in resp.content if bloco.type == "text").strip()

    def _gerar_gemini(self, mensagem: str) -> str:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise LLMIndisponivelError("SDK 'google-generativeai' não instalado.") from exc
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(self.modelo, system_instruction=config.SYSTEM_PROMPT_CLINICO)
        resp = model.generate_content(mensagem)
        return (resp.text or "").strip()
