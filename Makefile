.PHONY: help install dev test test-cov lint format clean docker-build docker-up docker-down migrate

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instalar dependencias en entorno virtual
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt

dev: ## Ejecutar servidor de desarrollo
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Ejecutar tests
	pytest tests/ -v

test-cov: ## Ejecutar tests con reporte de cobertura
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-watch: ## Ejecutar tests en modo watch
	pytest-watch tests/ -v

lint: ## Verificar código con linters
	flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	black --check app/ tests/
	isort --check-only app/ tests/

format: ## Formatear código
	black app/ tests/
	isort app/ tests/

clean: ## Limpiar archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	rm -f tests/test_db.sqlite tests/test_ci.db

docker-build: ## Construir imagen Docker
	docker compose build

docker-up: ## Levantar contenedores
	docker compose up -d

docker-down: ## Detener contenedores
	docker compose down

docker-logs: ## Ver logs de contenedores
	docker compose logs -f

migrate: ## Ejecutar migraciones
	alembic upgrade head

migrate-create: ## Crear nueva migración (usar: make migrate-create MSG="descripción")
	alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Revertir última migración
	alembic downgrade -1

db-reset: ## Resetear base de datos (¡CUIDADO!)
	alembic downgrade base
	alembic upgrade head

shell: ## Abrir shell de Python con contexto de la app
	python -c "from app.main import app; import IPython; IPython.embed()"
