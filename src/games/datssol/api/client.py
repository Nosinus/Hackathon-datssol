from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from datsteam_core.transport.http import HttpTransport
from games.datssol.models.raw import ArenaResponse, CommandRequest, CommandResponse, LogsOrError
from games.datssol.timeouts import DatsSolTimeoutPolicy


@dataclass(frozen=True)
class SubmitOutcome:
    transport_success: bool
    protocol_success: bool
    semantic_success: bool
    response: CommandResponse


@dataclass
class DatsSolClient:
    transport: HttpTransport
    timeout_policy: DatsSolTimeoutPolicy
    trace: list[dict[str, Any]] = field(default_factory=list)
    last_next_turn_in_seconds: float | None = None

    def arena(self) -> ArenaResponse:
        timeout = self.timeout_policy.arena_timeout(
            next_turn_in_seconds=self.last_next_turn_in_seconds
        )
        data = self.transport.get_validated("/api/arena", ArenaResponse, timeout_seconds=timeout)
        arena = cast(ArenaResponse, data)
        self.last_next_turn_in_seconds = float(arena.nextTurnIn)
        self.trace.append({"endpoint": "/api/arena", "method": "GET", "ok": True})
        return arena

    def command(
        self, payload: CommandRequest, *, next_turn_in_seconds: float | None
    ) -> CommandResponse:
        timeout = self.timeout_policy.command_timeout(next_turn_in_seconds=next_turn_in_seconds)
        response = self.transport.post_validated(
            "/api/command",
            payload.model_dump(exclude_none=True),
            CommandResponse,
            retryable=False,
            timeout_seconds=timeout,
        )
        self.trace.append(
            {
                "endpoint": "/api/command",
                "method": "POST",
                "request": payload.model_dump(exclude_none=True),
                "response": response.model_dump(exclude_none=True),
            }
        )
        return cast(CommandResponse, response)

    def submit_command(
        self, payload: CommandRequest, *, next_turn_in_seconds: float | None
    ) -> SubmitOutcome:
        response = self.command(payload, next_turn_in_seconds=next_turn_in_seconds)
        semantic_success = response.code == 0 and len(response.errors) == 0
        return SubmitOutcome(
            transport_success=True,
            protocol_success=response.code == 0,
            semantic_success=semantic_success,
            response=response,
        )

    def logs(self) -> LogsOrError:
        raw = self.transport.get_json(
            "/api/logs",
            timeout_seconds=self.timeout_policy.logs_timeout(),
        )
        parsed = LogsOrError.from_api_payload(raw)
        self.trace.append({"endpoint": "/api/logs", "method": "GET", "ok": True})
        return parsed
