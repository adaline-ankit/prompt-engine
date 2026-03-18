PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	pytest

evals:
	$(PYTHON) evals/runner.py

api:
	uvicorn prompt_engine.api.app:app --reload --host 0.0.0.0 --port 8000

cli:
	prompt-engine run "Extract the key business risks from this memo and return JSON."

mcp-stdio:
	prompt-engine mcp stdio

mcp-http:
	prompt-engine mcp http --host 127.0.0.1 --port 8001 --path /mcp

version:
	cat VERSION

bump-patch:
	$(PYTHON) scripts/release_bump.py --release-type patch

bump-minor:
	$(PYTHON) scripts/release_bump.py --release-type minor
