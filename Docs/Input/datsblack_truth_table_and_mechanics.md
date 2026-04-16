# DatsBlack truth table and mechanics brief

This is the most concrete currently available Datsteam prior.
It combines the DatsBlack mechanics document with the bundled OpenAPI contract summary.

Use DatsBlack as a **working exemplar adapter**, not as proof that DatsSol will use the same game.

## High-confidence facts

### Game type
- 2D naval combat / survival game.
- Tick-based multiplayer strategy.
- Teams control a fleet of ships via HTTP API.

### Tick semantics
- Tick duration is approximately **3 seconds**.
- During a tick, players can:
  - request state (`scan`),
  - submit ship commands,
  - optionally use remote scan.
- Commands are processed at the end of the current tick and before the next.

### Fleet structure
Each team has 10 ships:
- size 2: 4 ships
- size 3: 3 ships
- size 4: 2 ships
- size 5: 1 ship

Ships start with:
- speed 0
- a direction
- per-ship limits like `maxChangeSpeed`, `scanRadius`, `cannonRadius`, cooldowns, HP, etc.

### Movement
- Ships move only horizontally and vertically.
- They can rotate by `90` or `-90`.
- Rotation happens around the tail.
- If movement and rotation are both set, movement is resolved first, then rotation.
- Reverse movement is encoded as speed `-1`, but the backward movement speed is always 1 cell per tick.

### Observation
There are two scan mechanisms:

1. **Local scan**
   - each ship sees around itself,
   - scan center is the tail,
   - radius depends on ship characteristics.

2. **Long scan**
   - targeted remote scan around a chosen coordinate,
   - reveal lasts 5 ticks,
   - cooldown is 15 ticks,
   - radius is 60 cells.

### Shooting
- Each ship can shoot at a target coordinate within `cannonRadius` when cooldown allows.
- Damage zone is the chosen cell plus one cell around it (3x3 square).
- One successful hit event on a ship deals 1 damage regardless of how many ship cells were covered.
- The shell launches from the tail before movement.
- Hit registration happens after all ships move.
- Friendly fire is possible.

### Collisions
- Collision with island, shore, or same-size ship destroys the ship.
- Collision of different-size ships destroys the smaller ship and damages the larger by the smaller ship’s size.
- Collision handling is applied to each participant independently.

### Healing
- If a damaged ship avoids further damage for 8 ticks, it heals by 1.
- Continued safety keeps healing repeating every 8 ticks.

### Modes
1. **Deathmatch**
   - the fleet respawns after total destruction.

2. **Battle Royale**
   - a safe zone shrinks over time,
   - ships outside the zone start taking damage after 4 ticks outside,
   - re-entering the zone resets the outside counter,
   - for the first 10 ticks ships cannot take cannon damage, but collisions still happen.

### Scoring
Final score across final rounds depends on:
- placement / order of elimination,
- plus 1 point for each “honorable” enemy ship sunk.

“Honorable” sink rule:
- the enemy team must have shown enough activity,
- examples given in the doc: 500 travelled cells or hits on at least 2 ships.

Tie-break:
- compare last round placement, then previous rounds if needed.

### Important warning from the mechanics doc
Ship characteristics on final games **may differ from test games**.
Therefore:
- never hard-code example radii / cooldowns / speed limits,
- read them from the server state whenever possible.

## Canonical truth table

| Dimension | Current best answer |
|---|---|
| Interaction style | HTTP API, server-authoritative, tick-based |
| Observation | Partial; only scanned enemy info is visible |
| Action granularity | Per ship command bundle in one request |
| Action types | speed change, rotation, optional cannon shot |
| Simultaneity | Commands for all players are processed per tick |
| State certainty | Partial enemy knowledge, full own-ship knowledge |
| Hidden information | Enemy positions outside scan, future shrink timing, opponent intent |
| Delayed effects | shots resolve after movement; zone damage after outside timer |
| Static map | yes, islands / shore layout known |
| Dynamic global hazard | yes, shrinking zone in battle royale |
| Reward style | survival placement + honorable sinks |
| Parameter drift risk | yes; final ship stats may differ from test |

## What is concrete enough to implement tonight

A **DatsBlack adapter** can and should include:

- typed transport and schemas,
- canonical state for my ships, visible enemy ships, zone, map,
- occupancy / collision-risk helpers,
- legal ship-command builder,
- deterministic fallback,
- a safe baseline strategy,
- fixtures and tests built from the documented schema.

## Suggested safe exemplar baseline for DatsBlack

This is not “optimal”; it is the best conservative overnight starting point.

### Phase 1 — opening / first 10 ticks
Goals:
- avoid collisions,
- spread ships,
- move toward safe open water,
- collect scan information,
- do not rely on cannon damage during the first 10 ticks.

### Phase 2 — information and survival
Goals:
- keep ships away from islands / shore / same-tick self-blocking,
- maintain enough spacing to reduce friendly fire and chain collisions,
- use long scan to reveal likely contested regions or the path toward the shrinking zone,
- bias toward central / future-safe positions in battle royale.

### Phase 3 — opportunistic fire
Fire only when all are true:
- cooldown allows,
- predicted next-tick enemy location is plausible,
- target is within cannon radius,
- expected friendly-fire risk is low.

### Fallback action
If the strategy layer becomes uncertain:
- prefer no shot,
- prefer keeping the current safe heading,
- prefer speed changes that reduce immediate collision and zone risk,
- always emit a syntactically valid command bundle.

## What remains missing even for DatsBlack

- exact official placement-to-points table values are shown as an image in the original docs, not as clean text in the extracted sources,
- live network behavior, rate limits, and exact timeout semantics are not proven by the offline files,
- map loading details depend on `mapUrl`,
- true live server quirks cannot be tested in the offline Codex environment.

## Source notes

- Mechanics doc in repo: `Геймтон DatsBlack .docx`
- OpenAPI in repo: `openapi.json`
- Official documentation landing: `https://gamethon.datsteam.dev/DatsBlack/documentation/index.html`
