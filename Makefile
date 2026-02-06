.PHONY: help build run run-nested clean push pull status test test-unit test-pipeline test-pipeline-smoke check-artifacts setup-env ensure-dvc ensure-dvc-perms fix-dvc-perms lint fmt-check

ifneq (,$(wildcard .env))
include .env
export
endif

DOCKER_COMPOSE ?= docker-compose
HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)
PROJECT_PATH := $(CURDIR)
DVC_ENV := PROJECT_PATH=$(PROJECT_PATH) HOST_UID=$(HOST_UID) HOST_GID=$(HOST_GID)
UV_ENV := UV_CACHE_DIR=$(PROJECT_PATH)/.uv-cache UV_TOOL_DIR=$(PROJECT_PATH)/.uv-tools
DVC_HOST_CMD := $(shell if command -v uvx >/dev/null 2>&1; then echo "uvx dvc"; elif command -v dvc >/dev/null 2>&1; then echo "dvc"; fi)

help:
	@echo "Setup:"
	@echo "  make setup-env     - Create .env file"
	@echo "  make build         - Build Docker images"
	@echo ""
	@echo "Pipeline:"
	@echo "  make run           - Run pipeline from host/CI via DVC"
	@echo "  make run-nested    - Run pipeline via dvc-runner with docker socket opt-in"
	@echo "  make run-push      - Run pipeline + push to DagsHub"
	@echo "  make run-ingest    - Run ingest stage"
	@echo "  make run-preprocess- Run preprocess stage"
	@echo "  make run-train     - Run train stage"
	@echo "  make run-evaluate  - Run evaluate stage"
	@echo ""
	@echo "Data:"
	@echo "  make push          - Push to DagsHub"
	@echo "  make pull          - Pull from DagsHub"
	@echo "  make restore       - Restore everything from DagsHub"
	@echo "  make status        - Show status"
	@echo "  make dag           - Show DAG"
	@echo ""
	@echo "Other:"
	@echo "  make git-sync      - Commit and push to GitHub"
	@echo "  make clean         - Remove generated files"
	@echo "  make test          - Run unit + pipeline tests"
	@echo "  make lint          - Run ruff checks via uvx"
	@echo "  make fmt-check     - Check formatting via ruff format"
	@echo "  make fix-dvc-perms - Repair .dvc ownership using Docker"
	@echo ""

setup-env:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env"; else echo ".env exists"; fi

ensure-dvc:
	@if [ -z "$(DVC_HOST_CMD)" ]; then \
		echo "Neither 'dvc' nor 'uvx' found on host. Install DVC CLI or uv, or use 'make run-nested'."; \
		exit 1; \
	fi

ensure-dvc-perms:
	@if [ ! -w .dvc/tmp ]; then \
		echo ".dvc/tmp is not writable by current user."; \
		echo "Run 'make fix-dvc-perms' once, then retry."; \
		exit 1; \
	fi

fix-dvc-perms:
	@docker run --rm -v $(PROJECT_PATH):/repo alpine:3.20 sh -c "chown -R $(HOST_UID):$(HOST_GID) /repo/.dvc"

build:
	$(DOCKER_COMPOSE) build

run: ensure-dvc ensure-dvc-perms
	@$(DVC_ENV) $(DVC_HOST_CMD) repro

run-nested:
	@$(DVC_ENV) $(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.nested.yml run --rm dvc-runner dvc repro

run-push: run push

run-ingest: ensure-dvc ensure-dvc-perms
	@$(DVC_ENV) $(DVC_HOST_CMD) repro ingest

run-preprocess: ensure-dvc ensure-dvc-perms
	@$(DVC_ENV) $(DVC_HOST_CMD) repro preprocess

run-train: ensure-dvc ensure-dvc-perms
	@$(DVC_ENV) $(DVC_HOST_CMD) repro train

run-evaluate: ensure-dvc ensure-dvc-perms
	@$(DVC_ENV) $(DVC_HOST_CMD) repro evaluate

push: ensure-dvc ensure-dvc-perms
	@$(DVC_ENV) $(DVC_HOST_CMD) push

pull: ensure-dvc ensure-dvc-perms
	@$(DVC_ENV) $(DVC_HOST_CMD) pull

restore:
	@echo "🔄 Restoring from DagHub..."
	@$(MAKE) pull
	@echo "✅ Data restored! Run 'make run' to reproduce."

status: ensure-dvc ensure-dvc-perms
	@$(DVC_ENV) $(DVC_HOST_CMD) status

dag: ensure-dvc ensure-dvc-perms
	@$(DVC_ENV) $(DVC_HOST_CMD) dag

git-sync:
	@read -p "Commit message: " msg; git add .; git commit -m "$$msg"; git push origin main

clean:
	rm -rf data/raw/* data/processed/* models/*.pkl models/*.joblib metrics/*.json

clean-all: clean
	$(DOCKER_COMPOSE) down --rmi all

test-unit:
	@$(UV_ENV) pytest tests/test_lineage.py

test-pipeline:
	@$(MAKE) run
	@$(MAKE) check-artifacts

test-pipeline-smoke:
	@$(MAKE) run-preprocess
	@test -f data/raw/iris.csv
	@test -f data/processed/train.csv
	@test -f data/processed/test.csv

check-artifacts:
	test -f data/raw/iris.csv
	test -f data/processed/train.csv
	test -f data/processed/test.csv
	test -f models/model_metadata.json
	test -f metrics/metrics.json

test: test-unit test-pipeline

lint:
	@$(UV_ENV) uvx ruff check .

fmt-check:
	@$(UV_ENV) uvx ruff format --check .

reproduce:
	@$(DOCKER_COMPOSE) run --rm dvc-runner python scripts/reproduce_experiment.py $(MODEL) $(VERSION) $(ARGS)

reproduce-json:
	@if [ -z "$(FILE)" ]; then echo "Usage: make reproduce-json FILE=experiment_<run>.json [WORKTREE=/tmp/repro-<hash>]"; exit 1; fi
	@FILE=$(FILE) WORKTREE=$(WORKTREE) bash scripts/reproduce_from_json.sh
