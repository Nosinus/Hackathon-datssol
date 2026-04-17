PYTHON ?= python3

.PHONY: setup format lint typecheck test run-fixture

setup:
	$(PYTHON) -m pip install -e .[dev]

format:
	$(PYTHON) -m ruff format src tests

lint:
	$(PYTHON) -m ruff check src tests

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest -q

run-fixture:
	$(PYTHON) -m scripts.run_datsblack_fixture
