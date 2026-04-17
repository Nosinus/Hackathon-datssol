from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RoundContext:
    game: str
    round_id: str | None = None
    match_id: str | None = None


@dataclass(frozen=True)
class RuntimeStats:
    tick: int
    latency_ms: float | None = None
    validator_ok: bool = True
    non_success_result: bool = False


@dataclass(frozen=True)
class GatewayLogMeta:
    round: RoundContext
    stats: RuntimeStats
    extra: dict[str, object] = field(default_factory=dict)
