from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, ActionSink, CanonicalState, StateProvider
from games.datsblack.api.client import DatsBlackClient
from games.datsblack.canonical.state import to_canonical
from games.datsblack.models.raw import ShipsCommands


@dataclass
class DatsBlackStateProvider(StateProvider):
    client: DatsBlackClient

    def poll(self) -> CanonicalState:
        scan = self.client.scan()
        return to_canonical(scan).state


@dataclass
class DatsBlackActionSink(ActionSink):
    client: DatsBlackClient

    def submit(self, action: ActionEnvelope) -> dict[str, object]:
        commands = ShipsCommands.model_validate(action.payload)
        response = self.client.ship_command(commands)
        return response.model_dump(exclude_none=True)
