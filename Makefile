.DEFAULT_GOAL := help

PYTHON_VERSIONS = $(shell python3 supported_pythons.py)

.PHONY: help
help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "%-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: install
install: ## Sync development dependencies and install Git hooks
	uv sync --locked
	uv run --no-sync pre-commit install

.PHONY: lint
lint: ## Check lint and formatting
	uv run --locked ruff check .
	uv run --locked ruff format --check .

.PHONY: format
format: ## Apply lint fixes and formatting
	uv run --locked ruff check --fix .
	uv run --locked ruff format .

.PHONY: test
test: ## Run the unit tests
	uv run --locked python tests.py

.PHONY: test-all
test-all: ## Test with every supported Python version
	@for version in $(PYTHON_VERSIONS); do \
		uv run --locked --python $$version python tests.py -v || exit $$?; \
	done

.PHONY: coverage
coverage: ## Run tests with coverage and write coverage.xml
	uv run --locked coverage run --branch --source=massedit tests.py
	uv run --locked coverage report -m
	uv run --locked coverage xml

.PHONY: dist
dist: ## Build source and wheel distributions
	uv build

.PHONY: upgrade
upgrade: ## Upgrade locked dependencies and pre-commit hooks
	uv lock --upgrade
	uv run --locked pre-commit autoupdate

.PHONY: release
release: ## Bump the version and update the changelog
	uv run --locked cz bump --changelog --retry ${RELEASE_OPTIONS}

.PHONY: clean
clean: ## Remove generated build, test, and coverage files
	rm -rf build dist htmlcov .pytest_cache .coverage coverage.xml
