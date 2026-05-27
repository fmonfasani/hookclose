.PHONY: help dev install hooks lint format typecheck test test-all check \
        up up-data up-runtime down logs ps clean bootstrap bootstrap-db state

# Application packages type-checked / covered (mirror pyproject).
PKGS := runtime agents contracts events workflows memory sandbox observability scheduler tasks adapters

help:
	@echo "HookClose / AINE — make targets"
	@echo ""
	@echo "  Engineering:"
	@echo "    dev           Create venv-ready dev env: install [dev] + pre-commit hooks"
	@echo "    install       Install package with dev extras (editable)"
	@echo "    hooks         Install pre-commit hooks"
	@echo "    lint          ruff check + ruff format --check"
	@echo "    format        ruff --fix + ruff format (autofix)"
	@echo "    typecheck     mypy --strict on application packages"
	@echo "    test          pytest with coverage (excludes integration)"
	@echo "    test-all      pytest full suite incl. integration"
	@echo "    check         lint + typecheck + test (the CI gate)"
	@echo "    state         Print current runtime state (SYSTEM_STATE.json)"
	@echo ""
	@echo "  Runtime / Docker:"
	@echo "    up            docker compose up -d --build (all services)"
	@echo "    up-data       Start only postgres + redis"
	@echo "    up-runtime    Start scheduler, workflow-engine, opencode-worker"
	@echo "    down          docker compose down"
	@echo "    logs          Tail compose logs"
	@echo "    ps            List running containers"
	@echo "    bootstrap     Full bootstrap (data + db init + runtime)"
	@echo "    bootstrap-db  Initialize database schema"
	@echo "    clean         Remove caches and build artifacts"

# --- Engineering ----------------------------------------------------------

install:
	python -m pip install -U pip wheel
	python -m pip install -e ".[dev]"

hooks:
	pre-commit install

dev: install hooks
	@echo "Dev environment ready. Run 'make check' before pushing."

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

typecheck:
	mypy $(PKGS)

test:
	pytest -m "not integration" --cov --cov-report=term-missing

test-all:
	pytest --cov --cov-report=term-missing

check: lint typecheck test
	@echo "All quality gates passed."

state:
	python -c "from runtime.state import RuntimeStateStore as S; import json; print(json.dumps(S().load().model_dump(), indent=2))"

clean:
	python -c "import shutil,glob,os; [shutil.rmtree(p,ignore_errors=True) for p in glob.glob('**/__pycache__',recursive=True)+['.mypy_cache','.ruff_cache','.pytest_cache','htmlcov','build','dist']]; [os.remove(f) for f in glob.glob('coverage.xml')+glob.glob('.coverage*')]"

# --- Runtime / Docker -----------------------------------------------------

up:
	docker compose up -d --build

up-data:
	docker compose up -d postgres redis

up-runtime:
	docker compose up -d scheduler workflow-engine opencode-worker

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

bootstrap-db:
	python scripts/init_db.py

bootstrap:
	@echo "Bootstrapping HookClose runtime..."
	docker compose up -d postgres redis; sleep 10
	python scripts/init_db.py
	docker compose up -d scheduler workflow-engine opencode-worker
	docker compose ps
