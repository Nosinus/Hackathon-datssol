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

    def write_step(
        self,
        state: CanonicalState,
        action: ActionEnvelope,
        result: dict[str, object],
        *,
        request_payload: dict[str, object] | None = None,
        candidate_actions: list[dict[str, object]] | None = None,
        candidate_scores: list[dict[str, object]] | None = None,
        latency_ms: int | None = None,
        remaining_budget_ms: int | None = None,
        fallback_flags: dict[str, bool] | None = None,
        validation_flags: dict[str, bool] | None = None,
        parser_extras: dict[str, object] | None = None,
    ) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        nonce = uuid4().hex[:8]
        path = self.base_dir / f"tick_{state.tick:06d}_{ts}_{nonce}.json"
        envelope = from_runtime_step(
            session_id=self.session_id,
            round_id=self.round_id,
            state=state,
            action=action,
            result=result,
            request_payload=request_payload,
            candidate_actions=candidate_actions,
            candidate_scores=candidate_scores,
            latency_ms=latency_ms,
            remaining_budget_ms=remaining_budget_ms,
            fallback_flags=fallback_flags,
            validation_flags=validation_flags,
            parser_extras=parser_extras,
        )
        path.write_text(
            json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path
