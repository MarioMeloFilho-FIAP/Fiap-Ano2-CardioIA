# Conceitos — Fase 5: Chatbots, NLP e Assistentes Virtuais

Resumo da implementação do chatbot explicando estratégias tomadas.

## 1. Sistemas conversacionais: NLU, NLG e híbridos

- **NLU (Natural Language Understanding)** — *entender* a mensagem: descobrir a
  **intenção** e as **entidades**. É determinístico e previsível. No projeto:
  `chatbot/engine.py` (local) e `chatbot/watson_client.py` (Watson).
- **NLG (Natural Language Generation)** — *gerar* texto novo com um LLM. Flexível,
  porém não-determinístico e sujeito a **alucinação**. No projeto:
  `chatbot/llm_client.py` (opcional).
- **Híbrido** — combina os dois: o NLU garante os fluxos operacionais/de
  segurança (emergência, agendamento) e o NLG entra nas dúvidas clínicas e
  abertas (medicamento, hábitos, fatores de risco, dúvida aberta). É a
  arquitetura recomendada e a que adotamos
  (`chatbot/router.py`).

## 2. Intenção (intent), entidade (entity) e diálogo

- **Intenção (`#`)** — o que o usuário *quer* (ex.: `#agendar_consulta`). Um
  classificador aprende a partir de **frases-exemplo** (mín. 5). Ver
  `skill_cardio.json` → `intents`.
- **Entidade (`@`)** — *dado* extraído da frase (ex.: `@sintoma = dor no peito`),
  com **sinônimos** e **fuzzy match** (tolera erros de digitação). Ver
  `skill_cardio.json` → `entities`.
- **Árvore de diálogo** — nós com condições (`#intent`) avaliados de cima para
  baixo, com um nó de boas-vindas (`welcome`) e um fallback (`anything_else`).
- **Variáveis de contexto (`$`)** — memória da conversa; aqui persistida em
  SQLite (`chatbot/storage.py`).

## 3. Como o motor NLU local classifica (sem dependências pesadas)

1. **Normalização** — minúsculas, remoção de acentos e pontuação (`normalizar`).
2. **Similaridade** — para cada frase-exemplo, combina similaridade de sequência
   (`difflib.SequenceMatcher`) com **Jaccard de tokens**; a maior pontuação vence.
3. **Threshold** — abaixo de `CONFIANCA_MINIMA` (0,30) a intenção é tratada como
   *não reconhecida* e é enviada ao NLG.
4. **Entidades** — busca por sinônimos (substring + *fuzzy* leve).

É a mesma ideia dos exemplos ELIZA/Cleverbot,
mas dirigida pelo JSON do assistente.

## 4. Watson Assistant e a troca de provedor

O `skill_cardio.json` segue o formato de *skill/workspace* do **IBM Watson
Assistant** e pode ser importado no serviço. O `watson_client.py` cria sessão,
envia a mensagem (`AssistantV2.message`) e traduz a resposta para o mesmo
`ResultadoNLU` do motor local — o roteador não precisa saber quem interpretou.

Uma implementação local do NLU foi necessária pois houve problemas com o IBM cloud, ficando sem acesso (free tier terminou, pois não foi gerado codigo usando o email da fiap). Há um fallback em caso do watson estar indisponível

A camada NLG é **neutra**: `llm_client.py` suporta **OpenAI**, **Anthropic** e
**Gemini** com a mesma interface, escolhidos por `LLM_PROVIDER` (ou
auto-detectados pela chave presente). 

## 5. Governança em IA aplicada a um assistente de saúde

- **Transparência** — *disclaimer* em toda resposta; o usuário sabe que fala com
  um assistente e que não é diagnóstico.
- **Segurança by design** — guardrail de emergência determinístico; segredos só
  via ambiente; minimização de dados persistidos.
- **Rastreabilidade** — cada turno grava intenção, confiança e fonte da resposta.
- **Metric contract (exemplo):** *taxa de reconhecimento* = turnos com intenção
  reconhecida ÷ total; *fallback rate* = turnos em fallback ÷ total — ambas
  extraíveis da tabela `mensagens`.

