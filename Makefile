.PHONY: install lint format type test test-performance check migrate run docker-up docker-down

install:
	pip install -r requirements.txt -r requirements-dev.txt

lint:
	ruff check app tests migrations

format:
	ruff format app tests migrations

type:
	mypy --config-file mypy.ini

test:
	pytest -q

test-performance:
	pytest -q -m performance

check: lint type test

migrate:
	python -m app.migrate

run:
	python -m app.main

docker-up:
	docker compose up --build

docker-down:
	docker compose down