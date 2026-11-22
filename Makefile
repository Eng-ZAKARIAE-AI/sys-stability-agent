VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup run lint typecheck test clean

setup:
	python3 -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"
	if [ ! -f .env ]; then cp .env.example .env; fi
	mkdir -p logs

run:
	$(BIN)/sys-agent

lint:
	$(BIN)/ruff check src tests

typecheck:
	$(BIN)/mypy src

test:
	$(BIN)/pytest -v

clean:
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache
