from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.transport.http import HttpTransport
from games.datsblack.models.raw import (
    LongScanRequest,
    LongScanResponse,
    MapResponse,
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
        return self.transport.post_validated("/api/longScan", body, LongScanResponse)  # type: ignore[return-value]

    def ship_command(self, commands: ShipsCommands) -> ShipCommandResponse:
        return self.transport.post_validated(
            "/api/shipCommand",
            commands.model_dump(exclude_none=True),
            ShipCommandResponse,
        )  # type: ignore[return-value]
