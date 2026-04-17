from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from datsteam_core.config.settings import FullSettings


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    session_id: str
    policy_id: str
    config_hash: str
    git_sha: str
    mode: str
    environment: str
    created_at: str
    replay_dir: str

    def as_replay_metadata(self) -> dict[str, object]:
        return asdict(self)


def config_hash_from_settings(settings: FullSettings) -> str:
    payload = {
        "game": settings.app.game,
        "api_base_url": settings.app.api_base_url,
        "auth": {"mode": settings.app.auth.mode, "header_name": settings.app.auth.header_name},
        "runtime": {
            "timeout_seconds": settings.app.runtime.timeout_seconds,
            "retries": settings.app.runtime.retries,
            "replay_dir": str(settings.app.runtime.replay_dir),
            "backoff_initial_seconds": settings.app.runtime.backoff_initial_seconds,
            "backoff_multiplier": settings.app.runtime.backoff_multiplier,
            "backoff_max_seconds": settings.app.runtime.backoff_max_seconds,
            "accept_gzip": settings.app.runtime.accept_gzip,
            "send_margin_ms": settings.app.runtime.send_margin_ms,
        },
        "datsblack": {
            "mode": settings.datsblack.mode,
            "enable_long_scan": settings.datsblack.enable_long_scan,
            "map_cache_dir": str(settings.datsblack.map_cache_dir),
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def default_git_sha() -> str:
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        return output or "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def build_run_manifest(
    *,
    settings: FullSettings,
    policy_id: str,
    mode: str,
    environment: str,
    run_id: str | None = None,
    session_id: str | None = None,
    git_sha: str | None = None,
) -> RunManifest:
    return RunManifest(
        run_id=run_id or uuid4().hex,
        session_id=session_id or uuid4().hex,
        policy_id=policy_id,
        config_hash=config_hash_from_settings(settings),
        git_sha=git_sha or default_git_sha(),
        mode=mode,
        environment=environment,
        created_at=datetime.now(UTC).isoformat(),
        replay_dir=str(settings.app.runtime.replay_dir),
    )


def save_run_manifest(manifest: RunManifest, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_run_manifest(path: Path) -> RunManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Run manifest must be a JSON object")
    return RunManifest(
        run_id=str(payload["run_id"]),
        session_id=str(payload["session_id"]),
        policy_id=str(payload["policy_id"]),
        config_hash=str(payload["config_hash"]),
        git_sha=str(payload["git_sha"]),
        mode=str(payload["mode"]),
        environment=str(payload["environment"]),
        created_at=str(payload.get("created_at", "")),
        replay_dir=str(payload.get("replay_dir", "logs/replay")),
    )
