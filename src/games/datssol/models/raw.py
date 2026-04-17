from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatsSolBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class ErrorResponse(DatsSolBaseModel):
    code: int
    errors: list[str] = Field(default_factory=list)


class Plantation(DatsSolBaseModel):
    id: int
    position: list[int]
    isMain: bool = False
    isIsolated: bool = False
    immunityUntilTurn: int | None = None
    hp: int


class EnemyPlantation(DatsSolBaseModel):
    id: int
    position: list[int]
    hp: int


class CellState(DatsSolBaseModel):
    position: list[int]
    terraformationProgress: int
    turnsUntilDegradation: int | None = None


class ConstructionState(DatsSolBaseModel):
    position: list[int]
    progress: int


class BeaverLair(DatsSolBaseModel):
    id: int
    position: list[int]
    hp: int


class UpgradeTier(DatsSolBaseModel):
    name: str
    current: int
    max: int


class PlantationUpgrades(DatsSolBaseModel):
    points: int
    intervalTurns: int
    turnsUntilPoints: int
    maxPoints: int
    tiers: list[UpgradeTier] = Field(default_factory=list)


class MeteoForecast(DatsSolBaseModel):
    kind: str
    turnsUntil: int
    id: int | None = None
    forming: bool | None = None


class ArenaResponse(DatsSolBaseModel):
    turnNo: int
    nextTurnIn: float | int
    size: list[int]
    actionRange: int | None = None
    signalRange: int | None = None
    visionRange: int | None = None
    settlementLimit: int | None = None
    plantations: list[Plantation] = Field(default_factory=list)
    enemy: list[EnemyPlantation] = Field(default_factory=list)
    mountains: list[list[int]] = Field(default_factory=list)
    cells: list[CellState] = Field(default_factory=list)
    construction: list[ConstructionState] = Field(default_factory=list)
    beavers: list[BeaverLair] = Field(default_factory=list)
    plantationUpgrades: PlantationUpgrades | None = None
    meteoForecasts: list[MeteoForecast] = Field(default_factory=list)


class CommandItem(DatsSolBaseModel):
    path: list[list[int]]


class CommandRequest(DatsSolBaseModel):
    command: list[CommandItem] | None = None
    plantationUpgrade: str | None = None
    relocateMain: list[list[int]] | None = None

    def has_useful_action(self) -> bool:
        if isinstance(self.command, list) and len(self.command) > 0:
            return True
        if isinstance(self.plantationUpgrade, str) and self.plantationUpgrade.strip() != "":
            return True
        if isinstance(self.relocateMain, list) and len(self.relocateMain) >= 2:
            return True
        return False


class CommandResponse(DatsSolBaseModel):
    code: int
    errors: list[str] = Field(default_factory=list)

    def is_success(self) -> bool:
        return self.code == 0 and len(self.errors) == 0


class LogEntry(DatsSolBaseModel):
    time: str
    message: str


class LogsResponse(DatsSolBaseModel):
    logs: list[LogEntry] = Field(default_factory=list)


class LogsOrError(DatsSolBaseModel):
    logs: list[LogEntry] | None = None
    code: int | None = None
    errors: list[str] | None = None

    @classmethod
    def from_api_payload(cls, payload: Any) -> LogsOrError:
        if isinstance(payload, list):
            return cls(logs=[LogEntry.model_validate(item) for item in payload])
        return cls.model_validate(payload)


__all__ = [
    "ArenaResponse",
    "BeaverLair",
    "CellState",
    "CommandItem",
    "CommandRequest",
    "CommandResponse",
    "ConstructionState",
    "EnemyPlantation",
    "ErrorResponse",
    "LogEntry",
    "LogsOrError",
    "LogsResponse",
    "MeteoForecast",
    "Plantation",
    "PlantationUpgrades",
    "UpgradeTier",
]
