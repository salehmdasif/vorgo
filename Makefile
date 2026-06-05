.PHONY: run run-worker migrate migrate-down migration seed generate-keys test test-cov lint format docker-up docker-down

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	arq app.tasks.worker.WorkerSettings

migrate:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migration:
	alembic revision --autogenerate -m "$(msg)"

seed:
	python -m app.scripts.seed

generate-keys:
	python -m app.scripts.generate_keys

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html

lint:
	ruff check app/
	black --check app/

format:
	ruff check --fix app/
	black app/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

install:
	pip install -r requirements.txt
