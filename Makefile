.PHONY: help build run clean push pull status test setup-env

help:
	@echo "Setup:"
	@echo "  make setup         - Setup .env and dvc.yaml"
	@echo "  make setup-env     - Create .env file"
	@echo "  make setup-dvc     - Generate dvc.yaml with correct paths"
	@echo "  make build         - Build Docker images"
	@echo ""
	@echo "Pipeline:"
	@echo "  make run           - Run complete pipeline"
	@echo "  make run-ingest    - Run ingest stage"
	@echo "  make run-preprocess- Run preprocess stage"
	@echo "  make run-train     - Run train stage"
	@echo "  make run-evaluate  - Run evaluate stage"
	@echo ""
	@echo "Data:"
	@echo "  make push          - Push to DagsHub"
	@echo "  make pull          - Pull from DagsHub"
	@echo "  make status        - Show status"
	@echo "  make dag           - Show DAG"
	@echo ""
	@echo "Other:"
	@echo "  make git-sync      - Commit and push to GitHub"
	@echo "  make clean         - Remove generated files"
	@echo "  make test          - Run and verify"
	@echo ""

setup-env:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env"; else echo ".env exists"; fi

setup-dvc:
	@./generate-dvc-yaml.sh

setup: setup-env setup-dvc
	@echo "Setup complete"

build:
	docker-compose build

run:
	docker-compose run --rm dvc-runner dvc repro

run-ingest:
	docker-compose run --rm dvc-runner dvc repro ingest

run-preprocess:
	docker-compose run --rm dvc-runner dvc repro preprocess

run-train:
	docker-compose run --rm dvc-runner dvc repro train

run-evaluate:
	docker-compose run --rm dvc-runner dvc repro evaluate

push:
	docker-compose run --rm dvc-runner dvc push

pull:
	docker-compose run --rm dvc-runner dvc pull

status:
	docker-compose run --rm dvc-runner dvc status

dag:
	docker-compose run --rm dvc-runner dvc dag

git-sync:
	@read -p "Commit message: " msg; git add .; git commit -m "$$msg"; git push origin main

clean:
	rm -rf data/raw/* data/processed/* models/*.pkl models/*.joblib metrics/*.json

clean-all: clean
	docker-compose down --rmi all

test:
	@$(MAKE) run
	@test -f data/raw/iris.csv && echo "OK: raw data" || echo "FAIL: raw data"
	@test -f data/processed/train.csv && echo "OK: train data" || echo "FAIL: train data"
	@test -f data/processed/test.csv && echo "OK: test data" || echo "FAIL: test data"
	@test -f models/model_metadata.json && echo "OK: model metadata" || echo "FAIL: model metadata"
	@test -f metrics/metrics.json && echo "OK: metrics" || echo "FAIL: metrics"
