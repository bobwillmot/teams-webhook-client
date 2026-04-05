PYTHON := .venv/bin/python
PIP := $(PYTHON) -m pip
TEAMS_POST := .venv/bin/teams-post
PAYLOAD_FILE ?= payload.json
CARD_FILE ?= card.json

ifneq ($(wildcard .env),)
include .env
endif

export TEAMS_WEBHOOK_URL

.PHONY: help venv install install-requests example post post-json post-card doctor test freeze clean

help:
	@echo "Available targets:"
	@echo "  make venv              Create .venv using the project-selected Python"
	@echo "  make install           Install the project in editable mode into .venv"
	@echo "  make install-requests  Install the project with optional requests support"
	@echo "  make example           Run example.py using .venv"
	@echo "  make post MESSAGE=...  Send a text message with teams-post"
	@echo "  make post-json         Send a full Teams JSON payload file"
	@echo "  make post-card         Send an Adaptive Card JSON file"
	@echo "  make doctor           Verify local environment and webhook configuration"
	@echo "  make test             Run smoke tests"
	@echo "  make freeze           Show installed package versions in .venv"
	@echo "  make clean            Remove build artifacts"
	@echo ""
	@echo "Optional .env support: set TEAMS_WEBHOOK_URL in .env or your shell"

venv:
	python3 -m venv .venv

install: venv
	$(PIP) install -e .

install-requests: venv
	$(PIP) install -e '.[requests]'

example:
	$(PYTHON) example.py

post:
	@if [ -z "$(MESSAGE)" ]; then echo "Usage: make post MESSAGE='Hello from make'"; exit 1; fi
	@if [ -z "$(TEAMS_WEBHOOK_URL)" ]; then echo "TEAMS_WEBHOOK_URL is not set. Put it in .env or export it in your shell."; exit 1; fi
	$(TEAMS_POST) "$(MESSAGE)"

post-json:
	@if [ -z "$(TEAMS_WEBHOOK_URL)" ]; then echo "TEAMS_WEBHOOK_URL is not set. Put it in .env or export it in your shell."; exit 1; fi
	$(TEAMS_POST) --payload-file "$(FILE)$(if $(FILE),,$(PAYLOAD_FILE))"

post-card:
	@if [ -z "$(TEAMS_WEBHOOK_URL)" ]; then echo "TEAMS_WEBHOOK_URL is not set. Put it in .env or export it in your shell."; exit 1; fi
	$(TEAMS_POST) --payload-file "$(FILE)$(if $(FILE),,$(CARD_FILE))" --payload-type adaptive-card

doctor:
	@if [ ! -x "$(PYTHON)" ]; then echo "Missing virtual environment Python at $(PYTHON). Run 'make install' first."; exit 1; fi
	@if [ ! -x "$(TEAMS_POST)" ]; then echo "Missing teams-post at $(TEAMS_POST). Run 'make install' first."; exit 1; fi
	@if [ ! -f "$(PAYLOAD_FILE)" ]; then echo "Missing sample payload file: $(PAYLOAD_FILE)"; exit 1; fi
	@if [ ! -f "$(CARD_FILE)" ]; then echo "Missing sample card file: $(CARD_FILE)"; exit 1; fi
	@if [ -z "$(TEAMS_WEBHOOK_URL)" ]; then echo "TEAMS_WEBHOOK_URL is not set. Put it in .env or export it in your shell."; exit 1; fi
	@echo "Python: $$($(PYTHON) --version)"
	@echo "teams-post: $$($(TEAMS_POST) --help >/dev/null 2>&1 && echo ok || echo failed)"
	@echo "payload.json: ok"
	@echo "card.json: ok"
	@echo "TEAMS_WEBHOOK_URL: configured"

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

freeze:
	$(PIP) freeze

clean:
	rm -rf build dist *.egg-info .pytest_cache .coverage