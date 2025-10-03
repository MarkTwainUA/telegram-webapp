PYTHON := python3
PIP := pip
UVICORN := uvicorn

.PHONY: install fmt lint test run run-docker precommit

install:
	$(PIP) install -e .

fmt:
	ruff check --fix src tests || true
	black src tests

lint:
	ruff check src tests
	black --check src tests

test:
	pytest

run:
	$(UVICORN) app.main:app --app-dir src --host 0.0.0.0 --port 8000 --reload

run-docker:
	docker build -t mcp-telegram-server . && docker run --rm -p 8000:8000 --env-file .env mcp-telegram-server

precommit:
	pre-commit install
	pre-commit run --all-files
