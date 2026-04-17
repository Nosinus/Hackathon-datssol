from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.replay.store import ReplayWriter
from datsteam_core.types.core import (
    ActionSink,
    ActionValidator,
    StateProvider,
    Strategy,
    TickBudget,
)


@dataclass
class RuntimeLoop:
    state_provider: StateProvider
    strategy: Strategy
    action_validator: ActionValidator
    action_sink: ActionSink
    replay_writer: ReplayWriter

    def step(self) -> dict[str, object]:
        state = self.state_provider.poll()
        budget = TickBudget(tick=state.tick)
        proposed = self.strategy.choose_action(state, budget)
        action = self.action_validator.sanitize(proposed, state)
        result = self.action_sink.submit(action)
        self.replay_writer.write_step(state=state, action=action, result=result)
        return result
