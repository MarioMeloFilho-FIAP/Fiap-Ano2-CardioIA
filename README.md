# CardioIA — Assistente Cardiológico Inteligente


## 📑 Índice

- [🩺 Fase 5: Assistente Cardiológico Conversacional (Chatbot)](#-fase-5-assistente-cardiológico-conversacional-chatbot)
  - [💡 Problema e solução](#-problema-e-solução)
  - [🧩 Arquitetura (híbrida NLU e NLG)](#-arquitetura-híbrida-nlu-e-nlg)
  - [📦 Entregáveis](#-entregáveis)
  - [✨ Destaques](#-destaques)
  - [🚀 Como executar (não precisa de TensorFlow)](#-como-executar-não-precisa-de-tensorflow)
  - [📚 Documentação da Fase 5](#-documentação-da-fase-5)
- [🔬 Fase 4: Visão Computacional na Clínica](#-fase-4-visão-computacional-na-clínica)
  - [📦 Escopo entregue](#-escopo-entregue)
  - [🧰 Stack](#-stack)
  - [📁 Estrutura do repositório](#-estrutura-do-repositório)
  - [🚀 Como executar](#-como-executar)
  - [➕ Ir Além](#-ir-além)
  - [🧠 Decisões de projeto](#-decisões-de-projeto)
  - [🔒 Ética, governança e LGPD](#-ética-governança-e-lgpd)
- [👥 Integrantes](#-integrantes)
- [🎥 Apresentação em vídeo](#-apresentação-em-vídeo)

---

## 🩺 Fase 5: Assistente Cardiológico Conversacional (Chatbot)

### 💡 Problema e solução

Dados clínicos são difíceis de interpretar para o paciente. A solução é um
**assistente conversacional** (disciplina PCV — PLN, Chatbots & Virtual Agents)
que atende em **linguagem natural**, identifica a **intenção** e as **entidades**
clínicas da mensagem e responde de forma estruturada, ética e rastreável.

### 🧩 Arquitetura (híbrida NLU e NLG)

```
mensagem do paciente
      │
      ▼
   NLU  ──►  IBM Watson Assistant  (quando há credenciais WA_*)
            └► Motor NLU local     (fallback — lê o mesmo skill_cardio.json)
      │
      ▼   roteador aplica as políticas:
  1) guardrail de emergência   → resposta fixa "SAMU 192"  (nunca usa LLM)
  2) intenção operacional       → resposta determinística do diálogo
  3) dúvida clínica/aberta      → geração por LLM (NLG), se habilitado
  4) baixa confiança            → pedido de esclarecimento (fallback)
      │
      ▼
  disclaimer clínico + persistência em SQLite (rastreabilidade)
```

### 📦 Entregáveis

| Parte | Conteúdo | Onde |
|---|---|---|
| **Parte 1** | Backend do assistente (NLU/NLG, roteador, persistencia) + JSON do assistente | [`chatbot/`](chatbot/), [`chatbot/skill_cardio.json`](chatbot/skill_cardio.json), [`docs/RELATORIO_FASE5_PARTE1.md`](docs/RELATORIO_FASE5_PARTE1.md) |
| **Parte 2** | Interfaces: chat web (Flask) + aba no app mobile | [`chatbot/templates/chat.html`](chatbot/templates/chat.html), [`mobile/src/ChatScreen.tsx`](mobile/src/ChatScreen.tsx) |

### ✨ Destaques

- **Watson híbrido:** o [`skill_cardio.json`](chatbot/skill_cardio.json) é
  **importável no IBM Watson Assistant** e também lido por um **motor NLU local** —
  funciona offline e usa o Watson real quando há credenciais.
- **Guardrail de emergência:** sintomas graves → orientação determinística
  **SAMU 192**, nunca pelo LLM.
- **NLG neutra e opcional:** OpenAI / Anthropic / Gemini via `.env` (auto-detecção).
- **Governança:** disclaimer em toda resposta, segredos só via `.env`, histórico
  rastreável em **SQLite**.

### 🚀 Como executar (não precisa de TensorFlow)

Pré-requisito: [`uv`](https://docs.astral.sh/uv/) instalado.

```bash
make chat-venv     # cria o venv leve da Fase 5 (Flask) e instala as dependências
make chat          # sobe o assistente em http://localhost:5001
make chat-test     # roda a suíte de testes da Fase 5 (30 casos)
make chat-extras   # (opcional) instala IBM Watson + SDKs de LLM
```

Para a demo mobile: `make chat` em um terminal e `make mobile` em outro → aba
**Assistente**. Configuração opcional de Watson/LLM em
[`chatbot/.env.example`](chatbot/.env.example).

### 📚 Documentação da Fase 5

- 🧠 **Conceitos e estratégias da implementação:** [`docs/CONCEITOS_FASE5.md`](docs/CONCEITOS_FASE5.md)
- 📄 **Relatório do fluxo conversacional (Parte 1):** [`docs/RELATORIO_FASE5_PARTE1.md`](docs/RELATORIO_FASE5_PARTE1.md)
- 🎬 **Roteiro do vídeo:** [`docs/ROTEIRO_VIDEO_FASE5.md`](docs/ROTEIRO_VIDEO_FASE5.md)

---

## 🔬 Fase 4: Visão Computacional na Clínica

Pré-processa imagens médicas (raios-X de tórax), treina e avalia **CNNs** para
classificar entre `NORMAL` e `PNEUMONIA`, e apresenta o resultado em uma
**interface web Flask** e em um **app mobile (React Native)**, ambos com mapa de
calor **Grad-CAM** (interpretabilidade da decisão).

### 📦 Escopo entregue

| Parte | Conteúdo | Onde |
|---|---|---|
| **Parte 1** | Pipeline de pré-processamento e organização das imagens | `notebooks/parte1_preprocessamento.ipynb`, `src/preprocessing.py`, `docs/RELATORIO_PARTE1.md` |
| **Parte 2** | CNN do zero + Transfer Learning (VGG16), avaliação e protótipo | `notebooks/parte2_cnn_classificacao.ipynb`, `webapp/`, `docs/RELATORIO_PARTE2.md` |
| **Ir Além 1** | Ética e Governança: vieses do dataset + métricas de *fairness* | `notebooks/ir_alem1_fairness.ipynb`, `src/fairness.py`, `docs/RELATORIO_IR_ALEM1.md` |
| **Ir Além 2** | App mobile (React Native + Expo) consumindo a API Flask | `mobile/`, API JSON em `webapp/app.py` (`/api/predict`) |

📚 Explicação didática de **todos os conceitos** de ML/redes neurais:
[`docs/CONCEITOS.md`](docs/CONCEITOS.md).

### 🧰 Stack

- **Python 3.11** (TensorFlow não suporta o 3.14 do sistema — venv dedicado).
- **TensorFlow/Keras** — CNNs e VGG16 (`keras.applications`).
- **Flask** — protótipo web de apresentação.
- **scikit-learn / matplotlib / seaborn** — métricas e visualizações.
- **Dataset:** [Chest X-Ray Pneumonia (Kermany et al.)](https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia).

### 📁 Estrutura do repositório

```
chatbot/      Fase 5 — backend do assistente (NLU/NLG, roteador, storage) + chat web
src/          Fase 4 — utilidades (config, preprocessing, inference, gradcam, fairness)
notebooks/    Fase 4 — parte1, parte2 e ir_alem1_fairness
scripts/      Fase 4 — download_dataset.py (baixa o dataset e gera o subset)
webapp/       Fase 4 — app Flask: interface web + API JSON (/api/predict)
mobile/       app React Native + Expo (abas Assistente | Triagem raio-X)
models/       Fase 4 — modelos .keras (não versionados)
data/         Fase 4 — dataset e subset (não versionados)
docs/         relatórios e conceitos das duas fases
tests/        testes pytest (Fase 4: preprocessing/inference/fairness; Fase 5: engine/router/storage/skill)
```

### 🚀 Como executar

Pré-requisito: [`uv`](https://docs.astral.sh/uv/) instalado (gerencia o venv e o
Python 3.11 — `uv` baixa o interpretador se necessário).

```bash
make prep-venv     # cria o venv (Python 3.11) e instala as dependências
make dataset       # baixa o dataset e gera data/chest_xray_subset (balanceado)
make train         # executa parte1 e parte2 → gera models/*.keras e métricas em docs/
make web           # sobe o app Flask em http://localhost:5000
make test          # roda a suíte de testes
```

> O `make dataset` usa `kagglehub` (pode pedir autenticação Kaggle na 1ª vez). Sem
> acesso ao Kaggle, baixe o dataset manualmente e aponte a pasta:
> `export CHEST_XRAY_DIR=/caminho/para/chest_xray` antes de `make dataset`.

Para abrir os notebooks interativamente: `make jupyter`. Para subir **os dois
backends juntos** (visão :5000 + chatbot :5001): `make demo`.

### ➕ Ir Além

**Ir Além 1 — Ética e Governança (fairness).** Análise de vieses do dataset e
equidade do modelo por subtipo de pneumonia (bacteriana × viral). Relatório em
[`docs/RELATORIO_IR_ALEM1.md`](docs/RELATORIO_IR_ALEM1.md); métricas em
`src/fairness.py` (testadas em `tests/test_fairness.py`).

**Ir Além 2 — App mobile (React Native + Expo).** App em [`mobile/`](mobile/) que
consome a API JSON do Flask. A API expõe `GET /api/health` e `POST /api/predict`
(multipart `imagem` + `modelo`), retornando classe, confiança e Grad-CAM em
base64. Setup completo e troubleshooting em [`mobile/README.md`](mobile/README.md).

### 🧠 Decisões de projeto

- **Pré-processamento único** (`src/preprocessing.py`) usado por notebooks e Flask,
  evitando divergência treino/inferência. As imagens saem em RGB `224×224` [0,255];
  a normalização (`Rescaling 1/255`) é embutida **dentro de cada modelo**.
- **Transfer Learning em grafo plano** (VGG16 via `input_tensor`) para que o Grad-CAM
  acesse diretamente a última camada convolucional.
- **Subset balanceado e reduzido** para viabilizar treino local em CPU.

### 🔒 Ética, governança e LGPD

- Dataset público de pesquisa, sem dados pessoais identificáveis; uso educacional.
- A interface deixa explícito que é **apoio à decisão**, não diagnóstico.
- O Grad-CAM fornece **rastreabilidade** da predição (onde o modelo olhou),
  alinhado às boas práticas de IA confiável e auditável.

---

## 👥 Integrantes

| Nome | RM |
|---|---|
| Carlos Mário Vieira de Melo Filho | RM563769 |
| Stephanie Dias dos Santos | RM564315 |

## 🎥 Apresentação em vídeo

- **Fase 5 — Assistente Conversacional (até 3 min):** _[link a ser inserido]_
- **Fase 4 — Triagem visual de raios-X:** _[link a ser inserido]_
