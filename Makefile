SHELL := /bin/bash

# Gerenciador de pacotes/venv: uv (https://docs.astral.sh/uv/).
UV := uv

# venv dedicado em Python 3.11 (TensorFlow não suporta o python3 padrão = 3.14)
VENV_NAME := fiap_ano2_fase4_cap1_venv
VENV_BIN  := $(VENV_NAME)/bin
PYTHON    := $(VENV_BIN)/python3
PY311     := 3.11

# Fase 5 — chatbot: venv LEVE e independente (não precisa de TensorFlow).
CHAT_VENV := fiap_ano2_fase5_venv
CHAT_BIN  := $(CHAT_VENV)/bin
CHAT_PY   := $(CHAT_BIN)/python3
CHAT_TESTS := tests/test_engine.py tests/test_router.py tests/test_storage.py tests/test_skill_json.py

.DEFAULT_GOAL := help

.PHONY: all prep-venv shell dataset jupyter train web test clean help \
        chat-venv chat chat-test demo mobile

all: prep-venv
	source $(VENV_BIN)/activate && /bin/bash

prep-venv:
	$(UV) venv $(VENV_NAME) --python $(PY311)
	$(UV) pip install --python $(PYTHON) -r requirements.txt
	@echo ">> venv '$(VENV_NAME)' pronto (Python 3.11 + TensorFlow)."

dataset:
	source $(VENV_BIN)/activate && $(PYTHON) scripts/download_dataset.py

jupyter:
	source $(VENV_BIN)/activate && jupyter notebook notebooks/

# Executa os notebooks de ponta a ponta (gera os modelos .keras e os PNGs de métricas)
train:
	source $(VENV_BIN)/activate && \
		jupyter nbconvert --to notebook --execute --inplace notebooks/parte1_preprocessamento.ipynb && \
		jupyter nbconvert --to notebook --execute --inplace notebooks/parte2_cnn_classificacao.ipynb

web:
	source $(VENV_BIN)/activate && $(PYTHON) -m webapp.app

test:
	source $(VENV_BIN)/activate && $(PYTHON) -m pytest tests -q

# ------------------------------ Fase 5 (chatbot) ----------------------------
chat-venv:
	$(UV) venv $(CHAT_VENV) --python $(PY311)
	$(UV) pip install --python $(CHAT_PY) -r chatbot/requirements.txt
	@echo ">> venv '$(CHAT_VENV)' pronto (Flask + Watson + LLMs, sem TensorFlow)."

chat:
	$(CHAT_PY) -m chatbot.app

chat-test:
	$(CHAT_PY) -m pytest $(CHAT_TESTS) -q

# ------------------------------ Apresentação --------------------------------
# Sobe os DOIS backends de uma vez: visão (Fase 4, :5000) + chatbot (Fase 5, :5001).
# Rodamos SEM o reloader do Flask (um processo por app) para o grupo ser estável
# na apresentação. Ctrl+C encerra ambos (trap "kill 0" derruba o grupo).
demo:
	@echo ">> Fase 4 (visão) em http://localhost:5000  |  Fase 5 (chatbot) em http://localhost:5001"
	@echo ">> Ctrl+C encerra os dois. Para o app mobile, rode 'make mobile' em outro terminal."
	@bash -c 'trap "kill 0" EXIT INT TERM; \
		$(PYTHON) -c "from webapp.app import create_app; create_app().run(host=\"0.0.0.0\", port=5000)" & \
		$(CHAT_PY) -c "from chatbot.app import create_app; create_app().run(host=\"0.0.0.0\", port=5001)" & \
		wait'

# App mobile (Expo). Requer os backends no ar (make demo) para as duas abas.
mobile:
	cd mobile && npm install && npx expo start

clean:
	-rm -rf $(VENV_NAME) $(CHAT_VENV)

help:
	@echo "Targets disponíveis (execute com 'make <target>'):"
	@echo "  prep-venv   Cria o venv '$(VENV_NAME)' (Python 3.11) e instala requirements"
	@echo "  dataset     Baixa o Chest X-ray (Kermany) e gera o subset reduzido em data/"
	@echo "  jupyter     Abre o Jupyter Notebook apontando para notebooks/"
	@echo "  train       Executa parte1 e parte2 (gera models/*.keras e métricas em docs/)"
	@echo "  web         Sobe o app Flask de visão (http://localhost:5000)"
	@echo "  test        Roda a suíte de testes (tests/) dentro do venv"
	@echo "  --- Fase 5 (Assistente Cardiológico Conversacional) ---"
	@echo "  chat-venv   Cria o venv '$(CHAT_VENV)' (chatbot, sem TensorFlow)"
	@echo "  chat        Sobe o assistente Flask (http://localhost:5001)"
	@echo "  chat-test   Roda os testes da Fase 5 (engine/router/storage/skill)"
	@echo "  --- Apresentação ---"
	@echo "  demo        Sobe os DOIS backends juntos (visão :5000 + chatbot :5001)"
	@echo "  mobile      Inicia o app Expo (npm install + expo start)"
	@echo "  clean       Remove os venvs '$(VENV_NAME)' e '$(CHAT_VENV)'"
	@echo "  all         prep-venv + abre um shell com o venv ativado"
	@echo "  help        Exibe esta mensagem de ajuda"
