PYTHON ?= python3

.PHONY: setup format lint typecheck test run-fixture run-live-datsblack summarize-replay compare-strategies

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

run-live-datsblack:
	$(PYTHON) -m games.datsblack.live --dry-run --ticks 1

summarize-replay:
	$(PYTHON) -m scripts.summarize_replay

compare-strategies:
	$(PYTHON) -m scripts.compare_datsblack_strategies
