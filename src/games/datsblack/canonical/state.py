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
    metadata: dict[str, object] = {
        "zone": scan.scan.zone.model_dump() if scan.scan.zone else None,
        "directions": {str(s.id): _DIRECTION_TO_VEC[s.direction] for s in scan.scan.myShips},
    }
    return DatsBlackCanonicalState(
        state=CanonicalState(tick=scan.scan.tick, me=me, enemies=enemies, metadata=metadata)
    )
