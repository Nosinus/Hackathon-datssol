from __future__ import annotations

from datsteam_core.platform.gateway import GatewayLogMeta, RoundContext, RuntimeStats


def test_gateway_meta_scaffold() -> None:
    meta = GatewayLogMeta(
        round=RoundContext(game="datsblack", round_id="r1", match_id="m1"),
        stats=RuntimeStats(tick=10, latency_ms=42.5, validator_ok=True, non_success_result=False),
        extra={"source": "fixture"},
    )

    assert meta.round.game == "datsblack"
    assert meta.stats.tick == 10
    assert meta.extra["source"] == "fixture"
