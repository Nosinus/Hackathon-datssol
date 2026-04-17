from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.transport.http import HttpTransport
from games.datssol.models.raw import ArenaResponse, CommandRequest, CommandResponse, LogsOrError


@dataclass
class DatsSolClient:
    transport: HttpTransport

    def arena(self) -> ArenaResponse:
        return self.transport.get_validated("/api/arena", ArenaResponse)  # type: ignore[return-value]

    def command(self, payload: CommandRequest) -> CommandResponse:
        return self.transport.post_validated(
            "/api/command",
            payload.model_dump(exclude_none=True),
            CommandResponse,
            retryable=False,
        )  # type: ignore[return-value]

    def logs(self) -> LogsOrError:
        raw = self.transport.get_json("/api/logs")
        return LogsOrError.from_api_payload(raw)
