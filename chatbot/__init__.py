"""
Projeto : CardioIA — Fase 5 (Assistente Cardiológico Conversacional)
Pacote  : chatbot — backend do assistente conversacional (NLU + NLG híbrido)

Pacote autocontido (não importa `src/`, logo não arrasta TensorFlow). Reúne:
- engine   : motor NLU local que lê o mesmo `skill_cardio.json` do Watson
- watson_client : integração real com IBM Watson Assistant (quando há credenciais)
- llm_client    : camada NLG opcional (Anthropic/OpenAI/Gemini, via env)
- router   : orquestração (guardrail de emergência → diálogo → LLM → fallback)
- storage  : persistência de sessões e mensagens em SQLite
- app      : aplicação Flask (interface web + API JSON /api/chat)

Aviso clínico: protótipo acadêmico de APOIO — não realiza diagnóstico nem
prescrição e não substitui avaliação de um profissional de saúde.
"""
