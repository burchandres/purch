include .env

.PHONY: help
help: ## Display available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z0-9_-]+:.*## .*$$' Makefile | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## Build the docker image(s)
	@echo "Running make $@..."
	docker compose --file=docker-compose.yml build --force-rm

down: ## Bring down the docker containers
	@echo "Running make $@..."
	docker compose --file=docker-compose.yml --file=docker-compose.test.yml down

nuke: ## Bring down the docker containers and delete volumes
	@echo "Running make $@..."
	docker compose --file=docker-compose.yml --file=docker-compose.test.yml down --volumes

hard-refresh: nuke build up ## Bring down containers, nuke volumes, rebuild, bring up again

lint: ## Run both lint-format and lint-check
	@echo "Running make $@..."
	make lint-format
	make lint-check

lint-format: ## Lint the project with ruff
	@echo "Running make $@..."
	uv run ruff format ./purch

lint-check: ## Check the formatting and perform easy fixes
	@echo "Running make $@..."
	uv run ruff check ./purch

run-tests:
	@echo "Running make $@..."
	make up-tests
	docker compose --file=docker-compose.test.yml run test-purch pytest --cov=purch tests/ -v
	make down

setup: ## Set up venv and install dependencies
	@echo "Running make $@..."
	uv venv
	uv sync --dev
	@echo "Activate new virtual environment with source .venv/bin/activate"

up: ## Spin up docker containers to run application
	@echo "Running make $@..."
	docker compose --file=docker-compose.yml up -d

up-tests: ## Spin up containers for testing from test docker-compose file
	@echo "Running make $@..."
	make down
	docker compose --file=docker-compose.test.yml up -d --build
