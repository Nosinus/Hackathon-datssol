from __future__ import annotations

import os
from pathlib import Path

from datsteam_core.config.settings import load_from_env, load_from_yaml


def test_load_from_env_reads_process_env(monkeypatch) -> None:
    monkeypatch.setenv("DATASTEAM_API_BASE_URL", "https://env-only.test")
    monkeypatch.setenv("DATASTEAM_API_KEY", "token-from-env")
    monkeypatch.setenv("DATASTEAM_DATSBLACK_ENABLE_LONG_SCAN", "false")

    settings = load_from_env(env_file=None)
    assert settings.app.api_base_url == "https://env-only.test"
    assert settings.app.auth.token == "token-from-env"
    assert settings.datsblack.enable_long_scan is False


def test_load_from_env_reads_dotenv_file(tmp_path: Path, monkeypatch) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "\n".join(
            [
                "DATASTEAM_API_BASE_URL=https://dotenv.test",
                "DATASTEAM_API_KEY=token-from-dotenv",
                "DATASTEAM_RETRIES=3",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("DATASTEAM_API_BASE_URL", raising=False)
    monkeypatch.delenv("DATASTEAM_API_KEY", raising=False)
    monkeypatch.delenv("DATASTEAM_RETRIES", raising=False)

    settings = load_from_env(env_file=dotenv)
    assert settings.app.api_base_url == "https://dotenv.test"
    assert settings.app.auth.token == "token-from-dotenv"
    assert settings.app.runtime.retries == 3

    os.environ.pop("DATASTEAM_API_BASE_URL", None)
    os.environ.pop("DATASTEAM_API_KEY", None)
    os.environ.pop("DATASTEAM_RETRIES", None)


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
