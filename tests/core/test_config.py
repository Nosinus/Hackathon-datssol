from __future__ import annotations

from pathlib import Path

from datsteam_core.config.settings import load_from_yaml


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
