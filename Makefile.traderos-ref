SHELL := /bin/bash
PROJECT := traderos
PYTHON := python3
export PYTHONPATH := src:$(PYTHONPATH)

.PHONY: help setup test test-fast test-coverage lint lint-fix format format-check typecheck clean pre-commit pre-commit-install docker-build docker-up docker-down ci test-postgres test-postgres-up test-postgres-down

help:
	@echo 'TraderOS Development Commands'
	@echo '──────────────────────────────────────'
	@echo 'setup            Install all dependencies'
	@echo 'test             Run all tests with coverage'
	@echo 'test-fast        Run tests without coverage'
	@echo 'test-coverage    Run tests and open coverage report'
	@echo 'lint             Run ruff linter'
	@echo 'lint-fix         Run ruff linter with auto-fix'
	@echo 'format           Format code with black and isort'
	@echo 'format-check     Check formatting without changes'
	@echo 'typecheck        Run pyright type checker'
	@echo 'clean            Remove build artifacts and cache'
	@echo 'docker-build     Build Docker image'
	@echo 'docker-up        Start Docker services'
	@echo 'docker-down      Stop Docker services'
	@echo 'pre-commit       Run all pre-commit hooks on all files'
	@echo 'pre-commit-install  Install pre-commit hooks'
	@echo 'ci               Run full CI pipeline locally'
	@echo 'test-postgres-up    Start PostgreSQL test container'
	@echo 'test-postgres-down  Stop PostgreSQL test container'
	@echo 'test-postgres       Run PostgreSQL backend tests (requires running postgres)'

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install ruff black isort pytest pytest-cov pyright pre-commit
	pre-commit install

test:
	pytest --cov --cov-report=term --cov-report=html $(ARGS)

test-fast:
	pytest -x --tb=short $(ARGS)

test-coverage: test
	@echo "Coverage report: htmlcov/index.html"

lint:
	ruff check $(ARGS) .

lint-fix:
	ruff check --fix $(ARGS) .

format:
	black $(ARGS) .
	isort $(ARGS) .

format-check:
	black --check .
	isort --check .

typecheck:
	pyright $(ARGS)

clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf __pycache__/
	rm -rf .*/__pycache__/
	rm -rf */*/__pycache__/
	rm -rf */*/*/__pycache__/
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name 'test_*.db' -delete
	rm -f .coverage
	rm -f coverage.xml

pre-commit:
	pre-commit run --all-files

pre-commit-install:
	pre-commit install

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

test-postgres-up:
	docker compose --profile test up -d postgres-test

test-postgres-down:
	docker compose --profile test down

test-postgres: test-postgres-up
	@echo "Waiting for PostgreSQL to be ready..."
	@bash -c 'for i in $$(seq 1 10); do docker exec traderos-pg-test pg_isready -U traderos -q 2>/dev/null && break; sleep 1; done'
	python3 -m pytest tests/test_observability_postgres.py -v --tb=short --no-cov

ci: lint format-check typecheck test
	@echo 'CI pipeline passed.'
