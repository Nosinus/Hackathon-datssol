# Deployment contour (predoc)

## What is included
- `Dockerfile` for runtime/CLI/fixture workflows.
- `.dockerignore` to keep build context small.
- `compose.yaml` for local smoke-run with mounted `logs/` and `ops/`.

## Local machine
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m scripts.cli fixture-run
```

## Container smoke command
```bash
docker build -t datsteam-agent:predoc .
docker run --rm -v "$(pwd)/logs:/app/logs" datsteam-agent:predoc fixture-run
```

## Docker Compose smoke
```bash
docker compose up --build datsteam-agent
```

## VPS / cloud VM
1. Use a small Linux VM close to the game region.
2. Clone repo and use the same image/commands as local.
3. Keep `ops/manifests/` and `logs/` persisted across restarts.
4. For training rounds, prefer containerized run for reproducibility.

## What to choose
- **Training rounds:** local first, switch to nearest VPS only if benchmark latency is high.
- **Finals:** run on stable VPS/VM with known network path and pre-baked image.

## Benchmark + send margin check
```bash
python -m scripts.cli ops benchmark --url https://datsblack.datsteam.dev/api/scan --samples 10
```
Use `recommended_send_margin_ms` as a conservative baseline in config/env.
