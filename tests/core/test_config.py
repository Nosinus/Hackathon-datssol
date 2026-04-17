from __future__ import annotations

import os
from pathlib import Path

from datsteam_core.config.settings import load_from_env, load_from_yaml


def test_load_from_yaml(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        """
game: datsblack
api_base_url: https://example.test
auth:
  header_name: X-API-Key
  token: t
runtime:
  timeout_seconds: 2.0
  retries: 2
  replay_dir: logs/replay
  backoff_initial_seconds: 0.1
  backoff_multiplier: 1.5
  backoff_max_seconds: 2.5
  accept_gzip: false
  send_margin_ms: 40
datsblack:
  mode: royal
  enable_long_scan: false
  map_cache_dir: logs/maps
""".strip(),
        encoding="utf-8",
    )
    settings = load_from_yaml(cfg)
    assert settings.app.api_base_url == "https://example.test"
    assert settings.datsblack.enable_long_scan is False
    assert settings.app.runtime.backoff_multiplier == 1.5
    assert settings.app.runtime.accept_gzip is False
    assert settings.app.runtime.send_margin_ms == 40


def test_load_from_env_uses_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATASTEAM_API_BASE_URL", "https://env.example.test")
    monkeypatch.setenv("DATASTEAM_API_KEY", "env-token")
    monkeypatch.setenv("DATASTEAM_RETRIES", "3")
    settings = load_from_env(env_file=None)

    assert settings.app.api_base_url == "https://env.example.test"
    assert settings.app.auth.token == "env-token"
    assert settings.app.runtime.retries == 3


def test_load_from_env_keeps_existing_contract_and_optional_timeouts(monkeypatch) -> None:
    monkeypatch.setenv("DATASTEAM_TIMEOUT_SECONDS", "5.0")
    monkeypatch.setenv("DATASTEAM_SEND_MARGIN_MS", "100")
    monkeypatch.setenv("DATASTEAM_HOT_TIMEOUT_SECONDS", "0.45")
    monkeypatch.setenv("DATASTEAM_LOGS_TIMEOUT_SECONDS", "2.0")

    settings = load_from_env(env_file=None)

    assert settings.app.runtime.timeout_seconds == 5.0
    assert settings.app.runtime.send_margin_ms == 100
    assert settings.app.runtime.hot_timeout_seconds == 0.45
    assert settings.app.runtime.logs_timeout_seconds == 2.0


def test_load_from_env_reads_dotenv_file(tmp_path: Path, monkeypatch) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "DATASTEAM_API_BASE_URL=https://dotenv.example.test\nDATASTEAM_API_KEY=dotenv-token\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("DATASTEAM_API_BASE_URL", raising=False)
    monkeypatch.delenv("DATASTEAM_API_KEY", raising=False)
    previous_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        settings = load_from_env()
    finally:
        os.chdir(previous_cwd)

    assert settings.app.api_base_url == "https://dotenv.example.test"
    assert settings.app.auth.token == "dotenv-token"
