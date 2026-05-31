.PHONY: help install dev test lint format clean docker-build docker-up docker-down docker-logs security-check

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3.11
VENV := .venv
ACTIVATE := $(VENV)/bin/activate
PIP := $(VENV)/bin/pip

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)IndoGovRAG - Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(GREEN)Usage:\n  make <target>\n\n$(GREEN)Targets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

##@ Development Setup

install: ## Install Python dependencies
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	$(PYTHON) -m venv $(VENV)
	. $(ACTIVATE) && pip install --upgrade pip
	. $(ACTIVATE) && pip install -r requirements.txt
	. $(ACTIVATE) && pip install -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

install-all: install install-frontend ## Install all dependencies

##@ Development

dev: ## Start development server (backend)
	@echo "$(BLUE)Starting backend development server...$(NC)"
	. $(ACTIVATE) && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	@echo "$(BLUE)Starting frontend development server...$(NC)"
	cd frontend && npm run dev

dev-all: ## Start both backend and frontend (in separate terminals)
	@echo "$(YELLOW)Run these in separate terminals:$(NC)"
	@echo "  $(BLUE)make dev$(NC)          # Backend"
	@echo "  $(BLUE)make dev-frontend$(NC) # Frontend"

##@ Testing

test: ## Run Python tests with coverage
	@echo "$(BLUE)Running Python tests...$(NC)"
	. $(ACTIVATE) && pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-verbose: ## Run tests with verbose output
	@echo "$(BLUE)Running tests (verbose)...$(NC)"
	. $(ACTIVATE) && pytest tests/ -v -s --cov=src --cov-report=term-missing

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	. $(ACTIVATE) && pytest-watch tests/

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd frontend && npm test

test-all: test test-frontend ## Run all tests

##@ Code Quality

lint: ## Run Python linting (ruff)
	@echo "$(BLUE)Linting Python code...$(NC)"
	. $(ACTIVATE) && ruff check .
	@echo "$(GREEN)✓ Linting complete$(NC)"

lint-frontend: ## Run frontend linting
	@echo "$(BLUE)Linting frontend code...$(NC)"
	cd frontend && npm run lint
	@echo "$(GREEN)✓ Frontend linting complete$(NC)"

lint-all: lint lint-frontend ## Run all linting

format: ## Format Python code (ruff format)
	@echo "$(BLUE)Formatting Python code...$(NC)"
	. $(ACTIVATE) && ruff format .
	. $(ACTIVATE) && ruff check --fix .
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-frontend: ## Format frontend code (prettier)
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	cd frontend && npx prettier --write .
	@echo "$(GREEN)✓ Frontend code formatted$(NC)"

format-all: format format-frontend ## Format all code

type-check: ## Run Python type checking (mypy)
	@echo "$(BLUE)Type checking Python code...$(NC)"
	. $(ACTIVATE) && mypy src/ api/
	@echo "$(GREEN)✓ Type checking complete$(NC)"

security-check: ## Run security checks (bandit, safety)
	@echo "$(BLUE)Running security checks...$(NC)"
	. $(ACTIVATE) && bandit -r src/ api/ -ll
	. $(ACTIVATE) && safety check
	@echo "$(GREEN)✓ Security checks complete$(NC)"

check-all: lint type-check test security-check ## Run all checks (lint, type-check, test, security)

##@ Docker

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Containers started$(NC)"

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

docker-logs: ## Show Docker container logs
	docker-compose logs -f

docker-restart: docker-down docker-up ## Restart Docker containers

docker-clean: ## Remove Docker containers, volumes, and images
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	docker-compose down -v --rmi all
	@echo "$(GREEN)✓ Docker cleanup complete$(NC)"

##@ Deployment

deploy-staging: ## Deploy to staging (Fly.io)
	@echo "$(BLUE)Deploying to staging...$(NC)"
	flyctl deploy --config fly.toml --app indogovrag-staging
	@echo "$(GREEN)✓ Deployed to staging$(NC)"

deploy-production: ## Deploy to production (Fly.io)
	@echo "$(BLUE)Deploying to production...$(NC)"
	flyctl deploy --config fly.toml --app indogovrag-prod
	@echo "$(GREEN)✓ Deployed to production$(NC)"

##@ Maintenance

clean: ## Clean temporary files
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage *.log
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-frontend: ## Clean frontend build artifacts
	@echo "$(BLUE)Cleaning frontend artifacts...$(NC)"
	cd frontend && rm -rf .next/ out/ node_modules/.cache/
	@echo "$(GREEN)✓ Frontend cleanup complete$(NC)"

clean-all: clean clean-frontend ## Clean all temporary files

##@ Data Management

init-data: ## Initialize data directories
	@echo "$(BLUE)Initializing data directories...$(NC)"
	mkdir -p data/raw data/processed data/vector_db data/evaluations logs
	@echo "$(GREEN)✓ Data directories initialized$(NC)"

validate-data: ## Validate dataset
	@echo "$(BLUE)Validating dataset...$(NC)"
	. $(ACTIVATE) && python scripts/validate_dataset.py
	@echo "$(GREEN)✓ Dataset validation complete$(NC)"

##@ Documentation

docs: ## Generate API documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	. $(ACTIVATE) && pdoc src/ --output docs/_build/
	@echo "$(GREEN)✓ Documentation generated$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8001$(NC)"
	. $(ACTIVATE) && pdoc src/ --port 8001
