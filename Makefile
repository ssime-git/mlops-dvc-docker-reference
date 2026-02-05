.PHONY: help build run clean push pull status test setup-env

# Default target
help:
	@echo "MLOps Pipeline - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make setup-env     - Create .env file from template"
	@echo "  make build         - Build all Docker images"
	@echo ""
	@echo "Pipeline:"
	@echo "  make run           - Run complete DVC pipeline"
	@echo "  make run-ingest    - Run only ingest stage"
	@echo "  make run-preprocess- Run only preprocess stage"
	@echo "  make run-train     - Run only train stage"
	@echo "  make run-evaluate  - Run only evaluate stage"
	@echo ""
	@echo "DVC & Data:"
	@echo "  make push          - Push data to DagsHub storage"
	@echo "  make pull          - Pull data from DagsHub storage"
	@echo "  make status        - Show DVC pipeline status"
	@echo "  make dag           - Show pipeline DAG"
	@echo ""
	@echo "Git:"
	@echo "  make git-sync      - Add, commit, and push to GitHub"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Remove generated data and outputs"
	@echo "  make clean-all     - Remove all data, outputs, and Docker images"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run pipeline and verify outputs"
	@echo ""

# Setup
setup-env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file. Please edit it with your DagsHub credentials."; \
	else \
		echo "⚠️  .env file already exists."; \
	fi

# Build Docker images
build:
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "✅ All images built successfully"

# Run pipeline
run:
	@echo "🚀 Running complete DVC pipeline..."
	docker-compose run --rm dvc-runner dvc repro
	@echo "✅ Pipeline completed"

# Run individual stages
run-ingest:
	@echo "🔽 Running ingest stage..."
	docker-compose run --rm dvc-runner dvc repro ingest

run-preprocess:
	@echo "⚙️  Running preprocess stage..."
	docker-compose run --rm dvc-runner dvc repro preprocess

run-train:
	@echo "🎯 Running train stage..."
	docker-compose run --rm dvc-runner dvc repro train

run-evaluate:
	@echo "📊 Running evaluate stage..."
	docker-compose run --rm dvc-runner dvc repro evaluate

# DVC operations
push:
	@echo "📤 Pushing data to DagsHub..."
	docker-compose run --rm dvc-runner dvc push
	@echo "✅ Data pushed successfully"

pull:
	@echo "📥 Pulling data from DagsHub..."
	docker-compose run --rm dvc-runner dvc pull
	@echo "✅ Data pulled successfully"

status:
	@echo "📋 DVC Pipeline Status:"
	docker-compose run --rm dvc-runner dvc status

dag:
	@echo "📊 Pipeline DAG:"
	docker-compose run --rm dvc-runner dvc dag

# Git operations
git-sync:
	@read -p "Enter commit message: " msg; \
	git add .; \
	git commit -m "$$msg"; \
	git push origin main
	@echo "✅ Changes pushed to GitHub (will sync to DagsHub automatically)"

# Cleanup
clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf data/raw/* data/processed/* models/*.pkl models/*.joblib metrics/*.json
	@echo "✅ Cleaned data and outputs"

clean-all: clean
	@echo "🧹 Removing Docker images..."
	docker-compose down --rmi all
	@echo "✅ Full cleanup completed"

# Testing
test:
	@echo "🧪 Testing pipeline..."
	@$(MAKE) run
	@echo ""
	@echo "Verifying outputs..."
	@test -f data/raw/iris.csv && echo "✅ Raw data exists" || echo "❌ Raw data missing"
	@test -f data/processed/train.csv && echo "✅ Train data exists" || echo "❌ Train data missing"
	@test -f data/processed/test.csv && echo "✅ Test data exists" || echo "❌ Test data missing"
	@test -f models/model_metadata.json && echo "✅ Model metadata exists" || echo "❌ Model metadata missing"
	@test -f metrics/metrics.json && echo "✅ Metrics exist" || echo "❌ Metrics missing"
	@echo ""
	@echo "✅ Pipeline test completed"
