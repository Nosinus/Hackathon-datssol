from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from datsteam_core.transport.http import HttpTransport
from games.datssol.models.raw import ArenaResponse, CommandRequest, CommandResponse, LogsOrError


@dataclass(frozen=True)
class SubmitOutcome:
    transport_success: bool
    protocol_success: bool
    semantic_success: bool
    response: CommandResponse


@dataclass
class DatsSolClient:
    transport: HttpTransport
    trace: list[dict[str, Any]] = field(default_factory=list)

    def arena(self) -> ArenaResponse:
        data = self.transport.get_validated("/api/arena", ArenaResponse)
        self.trace.append({"endpoint": "/api/arena", "method": "GET", "ok": True})
        return cast(ArenaResponse, data)

    def command(self, payload: CommandRequest) -> CommandResponse:
        response = self.transport.post_validated(
            "/api/command",
            payload.model_dump(exclude_none=True),
            CommandResponse,
            retryable=False,
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

    def submit_command(self, payload: CommandRequest) -> SubmitOutcome:
        response = self.command(payload)
        semantic_success = response.code == 0 and len(response.errors) == 0
        return SubmitOutcome(
            transport_success=True,
            protocol_success=response.code == 0,
            semantic_success=semantic_success,
            response=response,
        )

    def logs(self) -> LogsOrError:
        raw = self.transport.get_json("/api/logs")
        parsed = LogsOrError.from_api_payload(raw)
        self.trace.append({"endpoint": "/api/logs", "method": "GET", "ok": True})
        return parsed
