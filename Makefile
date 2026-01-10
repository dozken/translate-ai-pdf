.PHONY: help setup run test-api-key test-translation clean format lint check info

# Auto-detect Python (use venv if available, otherwise system)
VENV_DIR := venv
ifeq ($(wildcard $(VENV_DIR)/bin/python),)
	PYTHON := python3
	PIP := pip3
else
	PYTHON := $(VENV_DIR)/bin/python
	PIP := $(VENV_DIR)/bin/pip
endif

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

help: ## Show available commands
	@echo "$(GREEN)Available commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

setup: ## Setup virtual environment and install dependencies
	@echo "$(GREEN)Setting up project...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		python3 -m venv $(VENV_DIR); \
		echo "$(GREEN)Virtual environment created$(NC)"; \
	fi
	@$(PIP) install --upgrade pip
	@$(PIP) install -e .
	@if [ -f ".env.example" ] && [ ! -f ".env" ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)Please edit .env file with your API keys$(NC)"; \
	fi
	@echo "$(GREEN)Setup complete!$(NC)"

run: ## Run the Streamlit application
	@echo "$(GREEN)Starting Streamlit...$(NC)"
	@if [ ! -f ".env" ]; then \
		if [ -f ".env.example" ]; then \
			cp .env.example .env; \
			echo "$(YELLOW)Please edit .env file with your API keys$(NC)"; \
		fi; \
	fi
	@if [ -d "$(VENV_DIR)" ] && [ -f "$(VENV_DIR)/bin/python" ]; then \
		$(VENV_DIR)/bin/python -m streamlit run app.py --server.headless true; \
	elif command -v python3 > /dev/null 2>&1; then \
		python3 -m streamlit run app.py --server.headless true; \
	else \
		echo "$(RED)Error: Python not found. Run 'make setup' first$(NC)"; \
		exit 1; \
	fi

test-api-key: ## Test if Google API key is valid
	@if [ ! -f ".env" ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		exit 1; \
	fi
	@if [ -d "$(VENV_DIR)" ] && [ -f "$(VENV_DIR)/bin/python" ]; then \
		$(VENV_DIR)/bin/python test_api_key.py; \
	elif command -v python3 > /dev/null 2>&1; then \
		python3 test_api_key.py; \
	else \
		echo "$(RED)Error: Python not found. Run 'make setup' first$(NC)"; \
		exit 1; \
	fi

test-translation: ## Run translation test
	@if [ ! -f ".env" ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		exit 1; \
	fi
	@if [ -d "$(VENV_DIR)" ] && [ -f "$(VENV_DIR)/bin/python" ]; then \
		$(VENV_DIR)/bin/python test_translation.py; \
	elif command -v python3 > /dev/null 2>&1; then \
		python3 test_translation.py; \
	else \
		echo "$(RED)Error: Python not found. Run 'make setup' first$(NC)"; \
		exit 1; \
	fi

format: ## Format code with black
	@if command -v black > /dev/null 2>&1; then \
		black .; \
	else \
		echo "$(YELLOW)black not installed. Run: pip install black$(NC)"; \
	fi

lint: ## Lint code with ruff
	@if command -v ruff > /dev/null 2>&1; then \
		ruff check .; \
	else \
		echo "$(YELLOW)ruff not installed. Run: pip install ruff$(NC)"; \
	fi

check: format lint ## Run format and lint checks

clean: ## Clean generated files and caches
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "test_translation_output.pdf" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

info: ## Show project information
	@echo "$(GREEN)Project Info:$(NC)"
	@echo "  Python: $$($(PYTHON) --version 2>&1)"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "  Virtual Environment: $(GREEN)Active$(NC)"; \
	else \
		echo "  Virtual Environment: $(YELLOW)Not created$(NC)"; \
	fi
	@if [ -f ".env" ]; then \
		echo "  .env file: $(GREEN)Exists$(NC)"; \
	else \
		echo "  .env file: $(RED)Missing$(NC)"; \
	fi

.DEFAULT_GOAL := help
