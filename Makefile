# Makefile
# Common commands for the public-data-research-agent project.
# Run `make help` to see all available commands.

.PHONY: help run test test-unit test-integration lint clean \
        kind-setup kind-deploy kind-teardown kind-logs kind-status

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "  Development:"
	@echo "    make run                Start the API server with hot reload"
	@echo "    make test               Run all unit tests"
	@echo "    make test-unit          Run unit tests only (no network calls)"
	@echo "    make test-integration   Run integration tests (requires network)"
	@echo "    make lint               Check code style"
	@echo "    make clean              Remove cache and compiled files"
	@echo ""
	@echo "  Kind (local Kubernetes):"
	@echo "    make kind-setup         Install Kind + kubectl, create cluster"
	@echo "    make kind-deploy        Build image, deploy to Kind cluster"
	@echo "    make kind-teardown      Delete the Kind cluster"
	@echo "    make kind-logs          Stream pod logs"
	@echo "    make kind-status        Show pod and service status"
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
	# Run integration tests against the real SCB API — requires internet
	pytest tests/test_scb_api.py -v

test-all:
	# Run every test including integration tests
	pytest tests/ -v

# ── Lint ──────────────────────────────────────────────────────────────────────

lint:
	# Install pyflakes if missing then check all source files
	pip install pyflakes --quiet
	python3 -m pyflakes src/research_agent/

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	# Remove Python cache files and pytest artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	@echo "Clean done."

# ── Kind cluster ──────────────────────────────────────────────────────────────

kind-setup:
	# Install Kind + kubectl and create the local cluster (run once)
	bash deploy/kind/scripts/setup.sh

kind-deploy:
	# Build image, load into Kind, apply manifests, wait for ready
	bash deploy/kind/scripts/deploy.sh

kind-teardown:
	# Delete the Kind cluster and all resources
	bash deploy/kind/scripts/teardown.sh

kind-logs:
	# Stream logs from the running pod
	kubectl logs -l app=research-agent -f

kind-status:
	# Show pod and service status
	kubectl get pods,svc -l app=research-agent

# ── Turtle cluster ────────────────────────────────────────────────────────────

turtle-deploy:
	# Build, push to Docker Hub, apply manifests to Turtle cluster
	bash deploy/turtle/scripts/deploy.sh

turtle-teardown:
	# Remove research agent from Turtle cluster
	bash deploy/turtle/scripts/teardown.sh

turtle-logs:
	# Stream logs from the running pod on Turtle
	kubectl logs -l app=research-agent -n workshop -f

turtle-status:
	# Show pod and service status on Turtle
	kubectl get pods,svc,ingress -n workshop
