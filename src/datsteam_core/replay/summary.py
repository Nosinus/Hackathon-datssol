from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReplaySummary:
    files: int
    tick_min: int | None
    tick_max: int | None
    action_count: int
    non_success_results: int

    def as_dict(self) -> dict[str, object]:
        return {
            "files": self.files,
            "tick_min": self.tick_min,
            "tick_max": self.tick_max,
            "action_count": self.action_count,
            "non_success_results": self.non_success_results,
        }


def summarize_replay_dir(replay_dir: Path) -> ReplaySummary:
    ticks: list[int] = []
    actions = 0
    non_success = 0

    files = sorted(replay_dir.glob("tick_*.json"))
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        tick = payload.get("tick")
        if isinstance(tick, int):
            ticks.append(tick)
        action = payload.get("action")
        if isinstance(action, dict):
            actions += 1
        result = payload.get("result")
        if isinstance(result, dict) and result.get("success") is not True:
            non_success += 1

    return ReplaySummary(
        files=len(files),
        tick_min=min(ticks) if ticks else None,
        tick_max=max(ticks) if ticks else None,
        action_count=actions,
        non_success_results=non_success,
    )
