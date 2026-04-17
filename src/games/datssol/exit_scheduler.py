from __future__ import annotations

from dataclasses import dataclass

from games.datssol.legal_actions import CandidateAction


@dataclass(frozen=True)
class ScheduledAction:
    candidate: CandidateAction
    adjusted_score: float
    exit_use_index: int


def schedule_candidates(
    candidates: list[CandidateAction], *, limit: int = 1
) -> list[ScheduledAction]:
    usage: dict[tuple[int, int], int] = {}
    scheduled: list[ScheduledAction] = []
    pool = sorted(candidates, key=lambda c: (-c.base_score, c.path[1], c.path[2]))
    while pool and len(scheduled) < limit:
        best_idx = 0
        best_score = -1.0
        for idx, item in enumerate(pool):
            count = usage.get(item.path[1], 0)
            adjusted = item.base_score * (0.85**count)
            if adjusted > best_score:
                best_score = adjusted
                best_idx = idx
        chosen = pool.pop(best_idx)
        count = usage.get(chosen.path[1], 0)
        usage[chosen.path[1]] = count + 1
        scheduled.append(
            ScheduledAction(
                candidate=chosen,
                adjusted_score=chosen.base_score * (0.85**count),
                exit_use_index=count,
            )
        )
    return scheduled
