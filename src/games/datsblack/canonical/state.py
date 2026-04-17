from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import CanonicalEntity, CanonicalState
from games.datsblack.models.raw import ScanResponse


@dataclass(frozen=True)
class DatsBlackCanonicalState:
    state: CanonicalState


_DIRECTION_TO_VEC = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}


def to_canonical(scan: ScanResponse) -> DatsBlackCanonicalState:
    me = tuple(CanonicalEntity(id=str(ship.id), x=ship.x, y=ship.y) for ship in scan.scan.myShips)
    enemies = tuple(
        CanonicalEntity(id=f"enemy_{idx}", x=ship.x, y=ship.y)
        for idx, ship in enumerate(scan.scan.enemyShips)
    )

    my_ships: dict[str, dict[str, object]] = {}
    for ship in scan.scan.myShips:
        my_ships[str(ship.id)] = {
            "x": ship.x,
            "y": ship.y,
            "size": ship.size,
            "hp": ship.hp,
            "max_hp": ship.maxHp,
            "direction": ship.direction,
            "direction_vec": _DIRECTION_TO_VEC[ship.direction],
            "speed": ship.speed,
            "max_speed": ship.maxSpeed,
            "min_speed": ship.minSpeed,
            "max_change_speed": ship.maxChangeSpeed,
            "cannon_cooldown": ship.cannonCooldown,
            "cannon_cooldown_left": ship.cannonCooldownLeft,
            "cannon_radius": ship.cannonRadius,
            "scan_radius": ship.scanRadius,
            "hits": ship.cannonShootSuccessCount,
        }

    enemy_ships: list[dict[str, object]] = []
    for enemy in scan.scan.enemyShips:
        enemy_ships.append(
            {
                "x": enemy.x,
                "y": enemy.y,
                "size": enemy.size,
                "hp": enemy.hp,
                "max_hp": enemy.maxHp,
                "direction": enemy.direction,
                "direction_vec": _DIRECTION_TO_VEC[enemy.direction],
                "speed": enemy.speed,
            }
        )

    metadata: dict[str, object] = {
        "zone": scan.scan.zone.model_dump() if scan.scan.zone else None,
        "my_ships": my_ships,
        "enemy_ships": enemy_ships,
    }
    return DatsBlackCanonicalState(
        state=CanonicalState(tick=scan.scan.tick, me=me, enemies=enemies, metadata=metadata)
    )
