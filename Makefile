PYTHON ?= python3

.PHONY: setup format lint typecheck test run-fixture run-live-datsblack summarize-replay compare-strategies contract-check offline-lab

setup:
	$(PYTHON) -m pip install -e .[dev]

format:
	$(PYTHON) -m ruff format src tests scripts

lint:
	$(PYTHON) -m ruff check src tests scripts

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest -q

contract-check:
	$(PYTHON) -m scripts.check_contract_consistency

run-fixture:
	$(PYTHON) -m scripts.run_datsblack_fixture

run-live-datsblack:
	$(PYTHON) -m games.datsblack.live --dry-run --ticks 1

summarize-replay:
	$(PYTHON) -m scripts.summarize_replay

compare-strategies:
	$(PYTHON) -m scripts.compare_datsblack_strategies


offline-lab:
	$(PYTHON) -m scripts.offline_decision_lab run-manifest tests/fixtures/offline_lab/scenario_manifest.json
