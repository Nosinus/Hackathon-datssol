from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AuthSettings:
    mode: str
    header_name: str
    token: str


@dataclass(frozen=True)
class RuntimeSettings:
    timeout_seconds: float
    retries: int
    replay_dir: Path
    backoff_initial_seconds: float
    backoff_multiplier: float
    backoff_max_seconds: float
    accept_gzip: bool
    send_margin_ms: int
    hot_timeout_seconds: float | None = None
    cold_timeout_seconds: float | None = None
    arena_timeout_seconds: float | None = None
    command_timeout_seconds: float | None = None
    logs_timeout_seconds: float | None = None


@dataclass(frozen=True)
class AppSettings:
    game: str
    api_base_url: str
    auth: AuthSettings
    runtime: RuntimeSettings


@dataclass(frozen=True)
class DatsBlackSettings:
    mode: str = "royal"
    enable_long_scan: bool = True
    map_cache_dir: Path = Path("logs/maps")


@dataclass(frozen=True)
class FullSettings:
    app: AppSettings
    datsblack: DatsBlackSettings


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        name = key.strip()
        if not name:
            continue
        normalized = value.strip().strip("'").strip('"')
        os.environ.setdefault(name, normalized)


def load_from_env(*, env_file: str | Path | None = ".env") -> FullSettings:
    if env_file is not None:
        _load_dotenv(Path(env_file))
    app = AppSettings(
        game=os.getenv("DATASTEAM_GAME", "datsblack"),
        api_base_url=os.getenv("DATASTEAM_API_BASE_URL", "https://datsblack.datsteam.dev"),
        auth=AuthSettings(
            mode="header_token",
            header_name=os.getenv("DATASTEAM_AUTH_HEADER", "X-API-Key"),
            token=os.getenv("DATASTEAM_API_KEY", "replace_me"),
        ),
        runtime=RuntimeSettings(
            timeout_seconds=float(os.getenv("DATASTEAM_TIMEOUT_SECONDS", "1.5")),
            retries=int(os.getenv("DATASTEAM_RETRIES", "1")),
            replay_dir=Path(os.getenv("DATASTEAM_REPLAY_DIR", "logs/replay")),
            backoff_initial_seconds=float(os.getenv("DATASTEAM_BACKOFF_INITIAL_SECONDS", "0.2")),
            backoff_multiplier=float(os.getenv("DATASTEAM_BACKOFF_MULTIPLIER", "2.0")),
            backoff_max_seconds=float(os.getenv("DATASTEAM_BACKOFF_MAX_SECONDS", "2.0")),
            accept_gzip=_env_bool("DATASTEAM_ACCEPT_GZIP", True),
            send_margin_ms=int(os.getenv("DATASTEAM_SEND_MARGIN_MS", "50")),
            hot_timeout_seconds=_optional_env_float("DATASTEAM_HOT_TIMEOUT_SECONDS"),
            cold_timeout_seconds=_optional_env_float("DATASTEAM_COLD_TIMEOUT_SECONDS"),
            arena_timeout_seconds=_optional_env_float("DATASTEAM_ARENA_TIMEOUT_SECONDS"),
            command_timeout_seconds=_optional_env_float("DATASTEAM_COMMAND_TIMEOUT_SECONDS"),
            logs_timeout_seconds=_optional_env_float("DATASTEAM_LOGS_TIMEOUT_SECONDS"),
        ),
    )
    datsblack = DatsBlackSettings(
        mode=os.getenv("DATASTEAM_DATSBLACK_MODE", "royal"),
        enable_long_scan=_env_bool("DATASTEAM_DATSBLACK_ENABLE_LONG_SCAN", True),
        map_cache_dir=Path(os.getenv("DATASTEAM_DATSBLACK_MAP_CACHE_DIR", "logs/maps")),
    )
    return FullSettings(app=app, datsblack=datsblack)


def load_from_yaml(path: str | Path) -> FullSettings:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config root must be object")
    auth = data["auth"]
    runtime = data["runtime"]
    app = AppSettings(
        game=str(data["game"]),
        api_base_url=str(data["api_base_url"]),
        auth=AuthSettings(
            mode=str(auth.get("mode", "header_token")),
            header_name=str(auth["header_name"]),
            token=str(auth["token"]),
        ),
        runtime=RuntimeSettings(
            timeout_seconds=float(runtime.get("timeout_seconds", 1.5)),
            retries=int(runtime.get("retries", 1)),
            replay_dir=Path(runtime.get("replay_dir", "logs/replay")),
            backoff_initial_seconds=float(runtime.get("backoff_initial_seconds", 0.2)),
            backoff_multiplier=float(runtime.get("backoff_multiplier", 2.0)),
            backoff_max_seconds=float(runtime.get("backoff_max_seconds", 2.0)),
            accept_gzip=bool(runtime.get("accept_gzip", True)),
            send_margin_ms=int(runtime.get("send_margin_ms", 50)),
            hot_timeout_seconds=_optional_float(runtime.get("hot_timeout_seconds")),
            cold_timeout_seconds=_optional_float(runtime.get("cold_timeout_seconds")),
            arena_timeout_seconds=_optional_float(runtime.get("arena_timeout_seconds")),
            command_timeout_seconds=_optional_float(runtime.get("command_timeout_seconds")),
            logs_timeout_seconds=_optional_float(runtime.get("logs_timeout_seconds")),
        ),
    )
    dcfg: dict[str, Any] = data.get("datsblack", {})
    return FullSettings(
        app=app,
        datsblack=DatsBlackSettings(
            mode=str(dcfg.get("mode", "royal")),
            enable_long_scan=bool(dcfg.get("enable_long_scan", True)),
            map_cache_dir=Path(dcfg.get("map_cache_dir", "logs/maps")),
        ),
    )


def _optional_env_float(name: str) -> float | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return None
    return float(raw)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        return float(value)
    return None
