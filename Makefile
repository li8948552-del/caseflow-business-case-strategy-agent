.PHONY: install lint test run worker docker-up

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .
	python -m compileall -q src tests

test:
	pytest -q

run:
	uvicorn caseflow.api:app --reload

worker:
	python -m caseflow.worker

docker-up:
	docker compose up --build
