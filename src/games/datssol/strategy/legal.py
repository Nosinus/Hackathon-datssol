from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, CanonicalState
from games.datssol.validator import DatsSolSemanticValidator


@dataclass
class DatsSolActionValidator:
    def sanitize(self, action: ActionEnvelope, state: CanonicalState) -> ActionEnvelope:
        result = DatsSolSemanticValidator().validate(action, state)
        return ActionEnvelope(tick=state.tick, payload=result.payload, reason=action.reason)
