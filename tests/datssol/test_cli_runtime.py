from __future__ import annotations

from scripts.cli import _recommended_turn_sleep_seconds


def test_recommended_turn_sleep_subtracts_cycle_latency() -> None:
    sleep_seconds = _recommended_turn_sleep_seconds(
        next_turn_in=0.9,
        cycle_latency_ms=180,
    )
    assert sleep_seconds is not None
    assert 0.73 <= sleep_seconds <= 0.75


def test_recommended_turn_sleep_has_floor() -> None:
    sleep_seconds = _recommended_turn_sleep_seconds(
        next_turn_in=0.2,
        cycle_latency_ms=500,
    )
    assert sleep_seconds == 0.05
