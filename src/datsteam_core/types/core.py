from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class TickBudget:
    tick: int
    deadline_ms: int | None = None


@dataclass(frozen=True)
class CanonicalEntity:
    id: str
    x: int
    y: int


@dataclass(frozen=True)
class CanonicalState:
    tick: int
    me: tuple[CanonicalEntity, ...]
    enemies: tuple[CanonicalEntity, ...]
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionEnvelope:
    tick: int
    payload: dict[str, object]
    reason: str


class Strategy(Protocol):
    def choose_action(self, state: CanonicalState, budget: TickBudget) -> ActionEnvelope: ...


class ActionValidator(Protocol):
    def sanitize(self, action: ActionEnvelope, state: CanonicalState) -> ActionEnvelope: ...


class StateProvider(Protocol):
    def poll(self) -> CanonicalState: ...


class ActionSink(Protocol):
    def submit(self, action: ActionEnvelope) -> dict[str, object]: ...
