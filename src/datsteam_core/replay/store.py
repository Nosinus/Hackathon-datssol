from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from datsteam_core.replay.schema import from_runtime_step
from datsteam_core.types.core import ActionEnvelope, CanonicalState


@dataclass
class ReplayWriter:
    base_dir: Path
    session_id: str = field(default_factory=lambda: uuid4().hex)
    round_id: str = "default-round"
    run_metadata: dict[str, object] = field(default_factory=dict)

    def write_step(
        self,
        state: CanonicalState,
        action: ActionEnvelope,
        result: dict[str, object],
        *,
        request_payload: dict[str, object] | None = None,
        strategy_id: str = "unknown_strategy",
        validator_result: dict[str, bool] | None = None,
        request_meta: dict[str, object] | None = None,
        response_meta: dict[str, object] | None = None,
        transport_error: dict[str, object] | None = None,
        fallback_used: bool = False,
        candidate_count: int = 0,
        candidate_actions: list[dict[str, object]] | None = None,
        candidate_scores: list[dict[str, object]] | None = None,
        latency_ms: int | None = None,
        remaining_budget_ms: int | None = None,
        fallback_flags: dict[str, bool] | None = None,
        validation_flags: dict[str, bool] | None = None,
        parser_extras: dict[str, object] | None = None,
    ) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        session_id = str(self.run_metadata.get("session_id", self.session_id))
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        nonce = uuid4().hex[:8]
        path = self.base_dir / f"tick_{state.tick:06d}_{ts}_{nonce}.json"
        envelope = from_runtime_step(
            session_id=session_id,
            round_id=self.round_id,
            state=state,
            action=action,
            result=result,
            request_payload=request_payload,
            strategy_id=strategy_id,
            validator_result=validator_result,
            request_meta=request_meta,
            response_meta=response_meta,
            transport_error=transport_error,
            fallback_used=fallback_used,
            candidate_count=candidate_count,
            candidate_actions=candidate_actions,
            candidate_scores=candidate_scores,
            latency_ms=latency_ms,
            remaining_budget_ms=remaining_budget_ms,
            fallback_flags=fallback_flags,
            validation_flags=validation_flags,
            parser_extras=parser_extras,
            run_metadata=self.run_metadata,
        )
        path.write_text(
            json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path
