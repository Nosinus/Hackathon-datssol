from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from datsteam_core.types.core import ActionEnvelope, CanonicalState


@dataclass
class ReplayWriter:
    base_dir: Path

    def write_step(
        self,
        state: CanonicalState,
        action: ActionEnvelope,
        result: dict[str, object],
    ) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        nonce = uuid4().hex[:8]
        path = self.base_dir / f"tick_{state.tick:06d}_{ts}_{nonce}.json"
        payload = {
            "tick": state.tick,
            "state": {
                "me": [entity.__dict__ for entity in state.me],
                "enemies": [entity.__dict__ for entity in state.enemies],
                "metadata": state.metadata,
            },
            "action": action.payload,
            "reason": action.reason,
            "result": result,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
