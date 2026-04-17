from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import CanonicalState


@dataclass(frozen=True)
class EvalFeatures:
    main_hp: int
    isolated_count: int
    near_settlement_limit: bool
    beaver_count: int


def extract_features(state: CanonicalState) -> EvalFeatures:
    plantations = state.metadata.get("plantations")
    settlement_limit = state.metadata.get("settlement_limit")
    main_hp = 0
    isolated = 0

    if isinstance(plantations, dict):
        for item in plantations.values():
            if not isinstance(item, dict):
                continue
            if bool(item.get("is_main", False)):
                main_hp = _safe_int(item.get("hp"), default=0)
            if bool(item.get("is_isolated", False)):
                isolated += 1

    limit = _safe_int(settlement_limit, default=999)
    near_limit = len(state.me) >= max(1, limit - 1)
    beavers = state.metadata.get("beavers")
    beaver_count = len(beavers) if isinstance(beavers, list) else 0
    return EvalFeatures(
        main_hp=main_hp,
        isolated_count=isolated,
        near_settlement_limit=near_limit,
        beaver_count=beaver_count,
    )


def _safe_int(value: object, *, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default
