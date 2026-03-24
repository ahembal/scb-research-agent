# Makefile
# Common commands for the public-data-research-agent project.
# Run `make help` to see all available commands.

.PHONY: help run test test-unit test-integration lint clean

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "  make run              Start the API server with hot reload"
	@echo "  make test             Run all unit tests"
	@echo "  make test-unit        Run unit tests only (no network calls)"
	@echo "  make test-integration Run integration tests (requires network + API key)"
	@echo "  make lint             Check code style with pyflakes"
	@echo "  make clean            Remove cache and compiled files"
	@echo ""

# ── Run ───────────────────────────────────────────────────────────────────────

run:
	# Start the FastAPI server with hot reload enabled
	uvicorn research_agent.main:app --reload --app-dir src

# ── Test ──────────────────────────────────────────────────────────────────────

test:
	# Run all unit tests (excludes integration tests that require network)
	pytest tests/ -v --ignore=tests/test_scb_api.py

test-unit:
	# Run only pure unit tests — no network, no API keys needed
	pytest tests/test_session_store.py tests/test_agent_flow.py tests/test_api_endpoints.py -v

test-integration:
	# Run integration tests against the real SCB API — requires internet access
	pytest tests/test_scb_api.py -v

test-all:
	# Run every test including integration tests
	pytest tests/ -v

# ── Lint ──────────────────────────────────────────────────────────────────────

lint:
	# Install pyflakes if missing, then check all source files
	pip install pyflakes --quiet
	python3 -m pyflakes src/research_agent/

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	# Remove Python cache files and pytest artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	@echo "Clean done."
