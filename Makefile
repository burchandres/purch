include .env 

.PHONY: help
help: ## Display available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z0-9_-]+:.*## .*$$' Makefile | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## Build the docker image(s)
	@echo "Running make $@..."
	docker-compose --file=docker-compose.yml build --force-rm

down: ## Bring down the docker containers
	@echo "Running make $@..."
	docker-compose --file=docker-compose.yml down

lint: ## Lint the backend portion of the project with ruff
	@echo "Running make $@..."
	uv run ruff format ./purch

lint-check: ## Check the backend formatting and perform easy fixes
	@echo "Running make $@..."
	uv run ruff check --fix ./purch

run-local: ## Run the app locally for faster development
	@echo "Running make $@..."
	make up-db
	uv run fastapi dev purch/main.py --port=8080

setup: ## Set up venv and install dependencies
	@echo "Running make $@..."
	uv venv
	uv sync
	@echo "Activate new virtual environment with source .venv/bin/activate"

up: ## Spin up docker containers to run application
	@echo "Running make $@..."
	docker-compose --file=docker-compose.yml up -d

up-db: ## Just spin up the postgres container instance
	@echo "Running make $@..."
	docker-compose --file=docker-compose.yml up -d postgres
