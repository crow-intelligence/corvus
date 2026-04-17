.PHONY: help install lint fmt typecheck test docs dvc-push dvc-pull install-skills clean

help:           ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install:        ## Install all dependencies and pre-commit hooks
	uv sync
	uv run pre-commit install

lint:           ## Run ruff linter
	uv run ruff check src/ tests/

fmt:            ## Format code with ruff
	uv run ruff format src/ tests/

typecheck:      ## Run ty type checker
	uv run ty check src/

test:           ## Run tests with pytest
	uv run pytest tests/ -v

docs:           ## Build Sphinx docs → docs/_build/html
	uv run sphinx-build -b html docs/ docs/_build/html

dvc-push:       ## Push data and models to GCS
	uv run dvc push

dvc-pull:       ## Pull data and models from GCS
	uv run dvc pull

install-skills: ## Install Claude Code skill packs per .claude/skills/MANIFEST.yaml
	uv run python scripts/install-skills.py

clean:          ## Remove build artifacts and caches
	rm -rf dist/ build/ docs/_build/ .pytest_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
