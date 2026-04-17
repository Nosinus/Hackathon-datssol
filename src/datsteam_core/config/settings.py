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


@dataclass(frozen=True)
class FullSettings:
    app: AppSettings
    datsblack: DatsBlackSettings


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def load_from_env() -> FullSettings:
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
        ),
    )
    datsblack = DatsBlackSettings(
        mode=os.getenv("DATASTEAM_DATSBLACK_MODE", "royal"),
        enable_long_scan=_env_bool("DATASTEAM_DATSBLACK_ENABLE_LONG_SCAN", True),
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
        ),
    )
    dcfg: dict[str, Any] = data.get("datsblack", {})
    return FullSettings(
        app=app,
        datsblack=DatsBlackSettings(
            mode=str(dcfg.get("mode", "royal")),
            enable_long_scan=bool(dcfg.get("enable_long_scan", True)),
        ),
    )
