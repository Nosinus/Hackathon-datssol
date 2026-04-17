# Dev Quickstart

## 1. Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 2. Configure
```bash
cp .env.example .env
# optionally edit config.sample.yaml
```

## 3. Run checks
```bash
make lint
make typecheck
make test
```

## 4. Run offline fixture evaluator
```bash
make run-fixture
```

## 5. Replay directory convention
- default directory: `logs/replay/`
- file pattern: `tick_<tick>_<timestamp>.json`
