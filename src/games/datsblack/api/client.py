from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.transport.http import HttpTransport
from games.datsblack.models.raw import (
    CommonResponse,
    LongScanRequest,
    LongScanResponse,
    MapResponse,
    RegistrationResponse,
    ScanResponse,
    ShipCommandResponse,
    ShipsCommands,
)


@dataclass
class DatsBlackClient:
    transport: HttpTransport

    def get_map(self) -> MapResponse:
        return self.transport.get_validated("/api/map", MapResponse)  # type: ignore[return-value]

    def scan(self) -> ScanResponse:
        return self.transport.get_validated("/api/scan", ScanResponse)  # type: ignore[return-value]

    def long_scan(self, x: int, y: int) -> LongScanResponse:
        body = LongScanRequest(x=x, y=y).model_dump()
        return self.transport.post_validated(
            "/api/longScan", body, LongScanResponse, retryable=True
        )  # type: ignore[return-value]

    def ship_command(self, commands: ShipsCommands) -> ShipCommandResponse:
        return self.transport.post_validated(
            "/api/shipCommand",
            commands.model_dump(exclude_none=True),
            ShipCommandResponse,
            retryable=False,
        )  # type: ignore[return-value]

    def register_deathmatch(self) -> RegistrationResponse:
        return self.transport.post_validated(
            "/api/deathMatch/registration", {}, RegistrationResponse, retryable=True
        )  # type: ignore[return-value]

    def register_royal(self) -> CommonResponse:
        return self.transport.post_validated(
            "/api/royalBattle/registration", {}, CommonResponse, retryable=True
        )  # type: ignore[return-value]

    def exit_deathmatch(self) -> CommonResponse:
        return self.transport.post_validated(
            "/api/deathMatch/exitBattle", {}, CommonResponse, retryable=False
        )  # type: ignore[return-value]
