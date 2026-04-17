from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, ActionSink, CanonicalState, StateProvider
from games.datssol.api.client import DatsSolClient
from games.datssol.canonical.state import to_canonical
from games.datssol.models.raw import CommandRequest


@dataclass
class DatsSolStateProvider(StateProvider):
    client: DatsSolClient

    def poll(self) -> CanonicalState:
        arena = self.client.arena()
        return to_canonical(arena).state


@dataclass
class DatsSolActionSink(ActionSink):
    client: DatsSolClient

    def submit(self, action: ActionEnvelope) -> dict[str, object]:
        payload = action.payload
        if not isinstance(payload, dict) or not payload:
            return {"code": 0, "errors": ["submit skipped: empty safe-hold action"]}

        request = CommandRequest.model_validate(payload)
        if not request.has_useful_action():
            return {"code": 0, "errors": ["submit skipped: no useful action"]}

        result = self.client.submit_command(request)
        out = result.response.model_dump(exclude_none=True)
        out["semantic_success"] = result.semantic_success
        return out
