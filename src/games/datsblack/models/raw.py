from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Direction = Literal["north", "south", "east", "west"]


class ErrorModel(BaseModel):
    message: str | None = None


class CommonResponse(BaseModel):
    success: bool
    errors: list[ErrorModel] | None = None


class RegistrationResponse(CommonResponse):
    pass


class Zone(BaseModel):
    x: int
    y: int
    radius: int


class MyShip(BaseModel):
    id: int
    x: int
    y: int
    size: int
    hp: int
    maxHp: int
    direction: Direction
    speed: int
    maxSpeed: int
    minSpeed: int
    maxChangeSpeed: int
    cannonCooldown: int
    cannonCooldownLeft: int
    cannonRadius: int
    scanRadius: int
    cannonShootSuccessCount: int = 0


class EnemyShip(BaseModel):
    x: int
    y: int
    hp: int
    maxHp: int
    size: int
    direction: Direction
    speed: int


class Scan(BaseModel):
    myShips: list[MyShip]
    enemyShips: list[EnemyShip]
    zone: Zone | None = None
    tick: int
    tickRemainMs: int | None = None
    tick_remain_ms: int | None = None
    remaining_budget_ms: int | None = None


class ScanResponse(BaseModel):
    scan: Scan
    success: bool
    errors: list[ErrorModel] | None = None


class MapResponse(BaseModel):
    mapUrl: str | None = None
    success: bool
    errors: list[ErrorModel] | None = None


class LongScanRequest(BaseModel):
    x: int
    y: int


class LongScanResponse(BaseModel):
    tick: int
    success: bool
    errors: list[ErrorModel] | None = None


class CannonShoot(BaseModel):
    x: int
    y: int


class ShipCommand(BaseModel):
    id: int
    changeSpeed: int | None = Field(default=None)
    rotate: int | None = Field(default=None)
    cannonShoot: CannonShoot | None = Field(default=None)


class ShipsCommands(BaseModel):
    ships: list[ShipCommand]


class ShipCommandResponse(BaseModel):
    tick: int
    success: bool
    errors: list[ErrorModel] | None = None
