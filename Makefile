# MindFoundry — judge-friendly Makefile
#
# Quickstart for a fresh clone:
#
#   export NVIDIA_NIM_API_KEY="nvapi-..."   # your own NIM key
#   make setup    # venv + pip + generate SQLite
#   make api      # start the retrieval API in the background
#   make demo     # run the end-to-end demo walkthrough
#
# Everything else (eval, doctor, stop, clean) is optional.
#
# Variables you may override:
#   NVIDIA_NIM_API_KEY   (required for live Nemotron synthesis)
#   NVIDIA_NIM_MODEL     default: nvidia/llama-3.3-nemotron-super-49b-v1.5
#   HOTELSIM_PORT        default: 8765
#   PYTHON               default: python3
#   VENV                 default: .venv

PYTHON        ?= python3
VENV          ?= .venv
VENV_BIN      := $(VENV)/bin
VENV_PY       := $(VENV_BIN)/python
VENV_PIP      := $(VENV_BIN)/pip
HOTELSIM_PORT ?= 8765
NVIDIA_NIM_MODEL ?= nvidia/llama-3.3-nemotron-super-49b-v1.5
API_PID_FILE  := reports/hotelsim-api.pid
API_LOG_FILE  := reports/hotelsim-api.log

export HOTELSIM_PORT
export NVIDIA_NIM_MODEL

# Pretty colors (only when stdout is a TTY)
ifneq (,$(findstring xterm,$(TERM))$(findstring screen,$(TERM)))
  C_GREEN  := \033[92m
  C_YELLOW := \033[93m
  C_RED    := \033[91m
  C_BOLD   := \033[1m
  C_DIM    := \033[2m
  C_END    := \033[0m
endif

.PHONY: help setup install venv generate api stop demo eval smoke discord doctor clean reset

help: ## Show this help
	@printf "$(C_BOLD)MindFoundry$(C_END) — make targets\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(C_GREEN)%-12s$(C_END) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf "\nMinimal path:\n"
	@printf "  $(C_DIM)export NVIDIA_NIM_API_KEY=nvapi-...$(C_END)\n"
	@printf "  $(C_DIM)make setup && make api && make demo$(C_END)\n"

# --- setup -----------------------------------------------------------------

$(VENV)/bin/activate: requirements.txt
	@printf "$(C_BOLD)==>$(C_END) creating venv at $(VENV)\n"
	@$(PYTHON) -m venv $(VENV)
	@$(VENV_PIP) install --quiet --upgrade pip
	@$(VENV_PIP) install --quiet -r requirements.txt
	@touch $(VENV)/bin/activate

venv: $(VENV)/bin/activate ## Create the Python venv

install: venv ## Install Python dependencies (alias for venv)

data/hotel_sim.sqlite: venv hotel_sim/generate.py
	@printf "$(C_BOLD)==>$(C_END) generating simulated hotel (SQLite + bilingual data)\n"
	@$(VENV_PY) -m hotel_sim.generate

generate: data/hotel_sim.sqlite ## Generate the simulated hotel SQLite + event stream

setup: venv generate ## Full first-time setup: venv + deps + SQLite
	@printf "$(C_GREEN)setup complete$(C_END). Next: $(C_BOLD)make api && make demo$(C_END)\n"

# --- runtime ---------------------------------------------------------------

api: venv generate ## Start the local retrieval API in the background (HOTELSIM_PORT, default 8765)
	@mkdir -p reports
	@if [ -f $(API_PID_FILE) ] && kill -0 $$(cat $(API_PID_FILE)) 2>/dev/null; then \
	  printf "$(C_YELLOW)API already running$(C_END) (pid $$(cat $(API_PID_FILE)) on port $(HOTELSIM_PORT))\n"; \
	else \
	  printf "$(C_BOLD)==>$(C_END) starting retrieval API on http://127.0.0.1:$(HOTELSIM_PORT)\n"; \
	  HOTELSIM_PORT=$(HOTELSIM_PORT) nohup $(VENV_PY) api/server.py > $(API_LOG_FILE) 2>&1 & echo $$! > $(API_PID_FILE); \
	  up=0; \
	  for i in 1 2 3 4 5 6 7 8 9 10; do \
	    sleep 1; \
	    if curl -sf "http://127.0.0.1:$(HOTELSIM_PORT)/health" >/dev/null 2>&1; then up=1; break; fi; \
	    if ! kill -0 $$(cat $(API_PID_FILE)) 2>/dev/null; then break; fi; \
	  done; \
	  if [ "$$up" = "1" ]; then \
	    printf "$(C_GREEN)API up$(C_END) — pid $$(cat $(API_PID_FILE)), logs in $(API_LOG_FILE)\n"; \
	  else \
	    printf "$(C_RED)API failed to start$(C_END) — see $(API_LOG_FILE)\n"; tail -20 $(API_LOG_FILE) 2>/dev/null || true; \
	    rm -f $(API_PID_FILE); exit 1; \
	  fi; \
	fi

stop: ## Stop the background retrieval API
	@if [ -f $(API_PID_FILE) ] && kill -0 $$(cat $(API_PID_FILE)) 2>/dev/null; then \
	  printf "$(C_BOLD)==>$(C_END) stopping API (pid $$(cat $(API_PID_FILE)))\n"; \
	  kill $$(cat $(API_PID_FILE)) && rm -f $(API_PID_FILE); \
	  printf "$(C_GREEN)stopped$(C_END)\n"; \
	else \
	  printf "$(C_DIM)no API pid recorded$(C_END)\n"; rm -f $(API_PID_FILE); \
	fi

demo: venv ## Run the end-to-end demo walkthrough (requires NVIDIA_NIM_API_KEY)
	@if [ -z "$$NVIDIA_NIM_API_KEY" ]; then \
	  printf "$(C_RED)NVIDIA_NIM_API_KEY is not set.$(C_END)\n"; \
	  printf "$(C_DIM)Get a key at https://build.nvidia.com/ and then:$(C_END)\n"; \
	  printf "$(C_DIM)  export NVIDIA_NIM_API_KEY=nvapi-...$(C_END)\n"; \
	  exit 1; \
	fi
	@$(MAKE) --no-print-directory api
	@$(VENV_PY) scripts/demo_walkthrough.py

eval: venv generate ## Run the 500-incident baseline evaluation
	@printf "$(C_BOLD)==>$(C_END) running 500-incident baseline evaluation\n"
	@mkdir -p reports
	@$(VENV_PY) -m hotel_sim.evaluate --limit 500 --out reports/eval-baseline-500.json
	@printf "$(C_GREEN)wrote$(C_END) reports/eval-baseline-500.json\n"

smoke: venv ## Quick Nemotron-only smoke test (no API server needed)
	@$(VENV_PY) -c "import os,sys,types,json; \
sys.path.insert(0,'scripts'); sys.path.insert(0,'.'); \
sys.modules['discord_utils']=types.SimpleNamespace(channel_ids=lambda:{},read=lambda *a,**k:[],send=lambda *a,**k:[{'id':'stub'}]); \
import importlib.util; \
spec=importlib.util.spec_from_file_location('b','scripts/nemotron_rag_bridge.py'); \
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); \
res=m.nemotron_synthesize('hello, who answers maintenance issues at NeMo Lodge?', {'citations':[],'recommended_route':[],'guardrail':'','detected_intents':[]}); \
print('USED NIM:',res['used_nim']); print('MODEL:  ',res['model']); print('ERROR:  ',res['error']); print(); print(res['text'][:600])"

discord: venv ## Drip one simulated incident into the live Discord channels (requires DISCORD_BOT_TOKEN)
	@if [ -z "$$DISCORD_BOT_TOKEN" ]; then \
	  printf "$(C_YELLOW)DISCORD_BOT_TOKEN not set$(C_END) — skipping live Discord drip.\n"; \
	  printf "$(C_DIM)The local demo walkthrough does not need Discord.$(C_END)\n"; \
	  exit 0; \
	fi
	@$(VENV_PY) scripts/drip_discord_incidents.py

# --- diagnostics -----------------------------------------------------------

doctor: ## Print environment diagnostics and what is/isn't ready
	@printf "$(C_BOLD)MindFoundry doctor$(C_END)\n"
	@printf "  python:        "; $(PYTHON) --version 2>&1 || printf "$(C_RED)missing$(C_END)\n"
	@printf "  venv:          "; [ -x "$(VENV_PY)" ] && printf "$(C_GREEN)ok$(C_END) ($(VENV_PY))\n" || printf "$(C_YELLOW)not built$(C_END) — run: make venv\n"
	@printf "  sqlite db:     "; [ -f data/hotel_sim.sqlite ] && printf "$(C_GREEN)present$(C_END)\n" || printf "$(C_YELLOW)missing$(C_END) — run: make generate\n"
	@printf "  nim key:       "; [ -n "$$NVIDIA_NIM_API_KEY" ] && printf "$(C_GREEN)set$(C_END) (length $${#NVIDIA_NIM_API_KEY})\n" || printf "$(C_RED)NOT SET$(C_END) — export NVIDIA_NIM_API_KEY=nvapi-...\n"
	@printf "  nim model:     $(NVIDIA_NIM_MODEL)\n"
	@printf "  port:          $(HOTELSIM_PORT)"
	@if command -v lsof >/dev/null 2>&1 && lsof -ti tcp:$(HOTELSIM_PORT) >/dev/null 2>&1; then \
	  printf " $(C_YELLOW)(in use by pid $$(lsof -ti tcp:$(HOTELSIM_PORT)))$(C_END)\n"; \
	else \
	  printf " $(C_GREEN)(free)$(C_END)\n"; \
	fi
	@printf "  api running:   "; \
	if [ -f $(API_PID_FILE) ] && kill -0 $$(cat $(API_PID_FILE)) 2>/dev/null; then \
	  printf "$(C_GREEN)yes$(C_END) (pid $$(cat $(API_PID_FILE)))\n"; \
	else \
	  printf "$(C_DIM)no$(C_END)\n"; \
	fi
	@printf "  discord token: "; [ -n "$$DISCORD_BOT_TOKEN" ] && printf "$(C_GREEN)set$(C_END) (optional)\n" || printf "$(C_DIM)not set (optional)$(C_END)\n"

# --- cleanup ---------------------------------------------------------------

clean: stop ## Remove generated state (SQLite, reports/*.json{l}, __pycache__)
	@printf "$(C_BOLD)==>$(C_END) cleaning generated state\n"
	@rm -f data/hotel_sim.sqlite data/hotel_sim.sqlite-journal data/hotel_sim.sqlite-wal data/hotel_sim.sqlite-shm
	@rm -f reports/*.json reports/*.jsonl reports/*.pid reports/*.log
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
	@printf "$(C_GREEN)cleaned$(C_END)\n"

reset: clean ## Full reset: clean + remove the venv
	@printf "$(C_BOLD)==>$(C_END) removing venv at $(VENV)\n"
	@rm -rf $(VENV)
	@printf "$(C_GREEN)reset complete$(C_END) — run: make setup\n"
