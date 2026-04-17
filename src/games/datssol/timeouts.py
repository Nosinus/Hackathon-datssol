from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatsSolTimeoutPolicy:
    base_timeout_seconds: float
    send_margin_ms: int
    hot_timeout_seconds: float | None = None
    cold_timeout_seconds: float | None = None
    arena_timeout_seconds: float | None = None
    command_timeout_seconds: float | None = None
    logs_timeout_seconds: float | None = None

    def arena_timeout(self, *, next_turn_in_seconds: float | None = None) -> float:
        return self._hot_timeout(
            explicit=self.arena_timeout_seconds,
            next_turn_in_seconds=next_turn_in_seconds,
        )

    def command_timeout(self, *, next_turn_in_seconds: float | None = None) -> float:
        return self._hot_timeout(
            explicit=self.command_timeout_seconds,
            next_turn_in_seconds=next_turn_in_seconds,
        )

    def logs_timeout(self) -> float:
        if self.logs_timeout_seconds is not None:
            return max(0.1, self.logs_timeout_seconds)
        if self.cold_timeout_seconds is not None:
            return max(0.1, self.cold_timeout_seconds)
        return max(0.1, self.base_timeout_seconds)

    def _hot_timeout(self, *, explicit: float | None, next_turn_in_seconds: float | None) -> float:
        if explicit is not None:
            return max(0.1, min(explicit, 0.60))
        if self.hot_timeout_seconds is not None:
            return max(0.1, min(self.hot_timeout_seconds, 0.60))

        capped_global = min(self.base_timeout_seconds, 0.60)
        if next_turn_in_seconds is None:
            return max(0.1, capped_global)

        available = max(0.1, next_turn_in_seconds - (self.send_margin_ms / 1000.0))
        dynamic = min(0.60, max(0.35, available * 0.75))
        return max(0.1, min(capped_global, dynamic))
