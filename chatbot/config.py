"""
Projeto : CardioIA — Fase 5 (Assistente Cardiológico Conversacional)
Módulo  : Configuração central — fonte única de constantes e leitura de ambiente

Concentra thresholds, textos de governança (disclaimers) e a leitura das
variáveis de ambiente que ativam recursos opcionais (Watson e LLM). Segredos
NUNCA aparecem aqui — apenas os NOMES das variáveis são lidos de os.environ.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Caminhos ---------------------------------------------------------------
PACKAGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PACKAGE_DIR.parent
SKILL_FILE = PACKAGE_DIR / "skill_cardio.json"

# Carrega o chatbot/.env ANTES de ler as variáveis abaixo. Fazer isso aqui (e não
# no app.py) garante que WA_*/*_API_KEY sejam vistos, já que este módulo lê o
# ambiente no momento do import. Sem python-dotenv instalado, usa só os exports.
try:
    from dotenv import load_dotenv

    load_dotenv(PACKAGE_DIR / ".env")
except ImportError:
    pass

DB_PATH = Path(os.getenv("CHATBOT_DB", ROOT_DIR / "chatbot_conversas.db"))

# --- Servidor ---------------------------------------------------------------
CHATBOT_PORT = int(os.getenv("CHATBOT_PORT", "5001"))

# --- NLU (motor local) ------------------------------------------------------
# Abaixo deste score de confiança, a intenção é tratada como não reconhecida
# (dispara esclarecimento/fallback ou, se habilitado, a camada NLG).
CONFIANCA_MINIMA = float(os.getenv("CHATBOT_CONFIANCA_MINIMA", "0.30"))

# Intenções de fluxo de negócio determinístico (respondidas SEMPRE pelo diálogo
# do skill_cardio.json, nunca pelo LLM) — previsibilidade em fluxos operacionais
# e de segurança.
INTENTS_DETERMINISTICOS = {
    "saudacao",
    "despedida",
    "emergencia",
    "sintomas",
    "agendar_consulta",
    "resultado_exame",
}

# Intenções elegíveis para geração por LLM (dúvidas clínicas e abertas): quando
# há chave de LLM, a resposta é gerada (NLG); sem chave (ou em falha), caem na
# resposta determinística do próprio intent no diálogo. Emergência e agendamento
# nunca entram aqui.
INTENTS_NLG = {
    "duvida_medicamento",
    "habitos_saudaveis",
    "fatores_risco",
    "duvida_aberta",
}

# Sintomas que, mesmo sem a intenção #emergencia, disparam o guardrail de
# emergência (segurança em primeiro lugar).
SINTOMAS_CRITICOS = {"dor no peito", "falta de ar", "desmaio", "suor frio"}

# --- Governança / ética (Cap07) --------------------------------------------
DISCLAIMER = (
    "⚠️ Sou um assistente virtual acadêmico de apoio e não substituo um "
    "profissional de saúde. Não faço diagnóstico nem prescrição. Em emergência, "
    "ligue 192 (SAMU)."
)

RESPOSTA_EMERGENCIA = (
    "🚨 ATENÇÃO: os sinais que você descreve podem indicar uma EMERGÊNCIA "
    "cardíaca. Ligue IMEDIATAMENTE para o SAMU (192) ou vá ao pronto-socorro "
    "mais próximo. Permaneça em repouso, não fique sozinho(a) e não dirija até "
    "o hospital."
)

RESPOSTA_FALLBACK = (
    "Não tenho certeza se entendi. Posso ajudar com: sintomas, agendamento de "
    "consultas, resultados de exames, dúvidas sobre medicamentos, fatores de "
    "risco e hábitos saudáveis. Poderia reformular a sua pergunta?"
)

# --- Watson Assistant (opcional) -------------------------------------------
WA_API_KEY = os.getenv("WA_API_KEY")
WA_URL = os.getenv("WA_URL")
WA_ASSISTANT_ID = os.getenv("WA_ASSISTANT_ID")
WA_VERSION = os.getenv("WA_VERSION", "2021-11-27")


def watson_habilitado() -> bool:
    """True quando há credenciais suficientes para usar o Watson Assistant."""
    return bool(WA_API_KEY and WA_URL and WA_ASSISTANT_ID)


# --- Camada NLG / LLM (opcional) -------------------------------------------
# Camada NEUTRA de provedor. Suporta 'openai', 'anthropic' e 'gemini'.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Provedor pode ser fixado por env (LLM_PROVIDER); se não, é auto-detectado
# pela chave de API presente (sem privilegiar nenhum fornecedor).
_CHAVES_LLM = {"openai": OPENAI_API_KEY, "anthropic": ANTHROPIC_API_KEY, "gemini": GEMINI_API_KEY}


def _detectar_provider() -> str:
    fixado = os.getenv("LLM_PROVIDER", "").lower().strip()
    if fixado:
        return fixado
    for provider, chave in _CHAVES_LLM.items():
        if chave:
            return provider
    return ""


LLM_PROVIDER = _detectar_provider()

# Modelo por provedor (ajustável por env; default resolvido no llm_client).
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT_CLINICO = (
    "Você é o assistente virtual do CardioIA, um serviço acadêmico de apoio ao "
    "paciente em cardiologia. Responda em português do Brasil, em linguagem "
    "simples e acolhedora, de forma breve (no máximo 2 parágrafos curtos). "
    "Explique conceitos de saúde cardiovascular de forma educativa. NUNCA forneça "
    "diagnóstico, NUNCA prescreva ou ajuste medicamentos e NUNCA substitua a "
    "avaliação de um médico — sempre recomende procurar um profissional de saúde. "
    "Se a pergunta sugerir uma emergência (dor no peito intensa, falta de ar "
    "grave, desmaio), oriente ligar imediatamente para o SAMU (192). Não invente "
    "dados clínicos do paciente."
)


def llm_habilitado() -> bool:
    """True quando há um provedor resolvido e chave de API correspondente."""
    return bool(LLM_PROVIDER and _CHAVES_LLM.get(LLM_PROVIDER))
