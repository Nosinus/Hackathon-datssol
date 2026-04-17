# Current Truth Table (as of April 17, 2026, offline pack)

| Topic | Known now | Confidence | Source basis |
|---|---|---|---|
| DatsSol loop style | HTTP/JSON server-authoritative loop | High | Event snapshot |
| DatsSol schema | Unknown (not released in this repo) | High | Event snapshot |
| DatsBlack auth | `X-API-Key` header | High | OpenAPI |
| DatsBlack key endpoints | `/api/map`, `/api/scan`, `/api/longScan`, `/api/shipCommand`, registration/exit endpoints | High | OpenAPI |
| DatsBlack state shape | `myShips`, `enemyShips`, `zone`, `tick` | High | OpenAPI |
| DatsBlack action shape | per-ship command bundle (`changeSpeed`, `rotate`, `cannonShoot`) | High | OpenAPI + mechanics brief |
| DatsBlack operational harness | live CLI with env/YAML config, dry-run, scan-only, replay, map cache | High | implementation in repo |
| Transport hardening | retries/backoff for safe calls + timeout/status/schema error classes | High | implementation in repo |
| DatsBlack timing prior | ticked loop (~3 sec), command resolve per tick | Medium | mechanics brief |
| DatsBlack battle-royale prior | shrinking safe zone | Medium | mechanics brief |
| Snake3D transfer prior | timing + partial observability + command overwrite patterns may exist in ecosystem | Medium | warmup summary |
| Live infra behavior | exact timeout/rate-limit quirks unknown offline | High uncertainty | missing live env |

## What this table is for
- Keep implementation grounded in concrete known contract details.
- Prevent over-claims about unreleased DatsSol mechanics.
- Separate implemented DatsBlack exemplar features from DatsSol unknowns.
