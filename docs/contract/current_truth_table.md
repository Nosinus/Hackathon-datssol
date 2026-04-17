# Current Truth Table (as of 2026-04-16, offline pack)

| Topic | Known now | Confidence | Source basis |
|---|---|---|---|
| DatsSol loop style | HTTP/JSON server-authoritative loop | High | Event snapshot |
| DatsSol schema | Unknown (not released yet) | High | Event snapshot |
| DatsBlack auth | `X-API-Key` header | High | OpenAPI |
| DatsBlack key endpoints | `/api/map`, `/api/scan`, `/api/longScan`, `/api/shipCommand` | High | OpenAPI |
| DatsBlack state shape | `myShips`, `enemyShips`, `zone`, `tick` | High | OpenAPI |
| DatsBlack action shape | per-ship command bundle (`changeSpeed`, `rotate`, `cannonShoot`) | High | OpenAPI + mechanics brief |
| DatsBlack timing prior | ticked loop (~3 sec), command resolve per tick | Medium | mechanics brief |
| DatsBlack battle-royale prior | shrinking safe zone | Medium | mechanics brief |
| Snake3D transfer prior | timing + partial observability + command overwrite patterns may exist in ecosystem | Medium | warmup summary |
| Live infra behavior | exact timeout/rate-limit quirks unknown offline | High uncertainty | missing live env |

## What this table is for
- Keep implementation grounded in what is concrete now.
- Prevent accidental over-claims about unreleased DatsSol rules.
