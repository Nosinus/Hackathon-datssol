# Snake3D / DatsNewWay warm-up summary

This file condenses the warm-up PDF into a text-first brief for Codex.
Use it as a **Datsteam organizer-style prior**, not as the final DatsSol contract.

## What is concrete in the warm-up

### Server and interaction pattern
- The game server is reached over HTTP.
- The warm-up shows a Swagger/OpenAPI link.
- Requests use header `X-Auth-Token`.
- The main interaction example is `POST /api/move`.
- Sending an empty `snakes` array is allowed to query the current situation without changing directions.
- Gzip responses are explicitly mentioned as useful for reducing payload size.

### Tick structure
- The game is tick-based.
- Each tick is approximately **1 second** (may change).
- Players submit commands for the next move during the tick.
- At the end of the tick the server processes commands.

### State fields mentioned in the warm-up
Common response fields include:

- `mapSize`
- `name`
- `points`
- `fences`
- `snakes`
- `enemies`
- `food`
- `specialFood`
- `turn`
- `tickRemainMs`
- `reviveTimeoutSec`
- `errors`

Snake fields mentioned include:

- `id`
- `direction`
- `oldDirection`
- `geometry`
- `deathCount`
- `status`
- `reviveRemainMs`

### Movement and control
- The map is **3D**.
- The player starts with **3 snakes** of length 1.
- Direction commands are vectors like `[1,0,0]` or `[0,0,-1]`.
- Invalid control parameters are ignored for the affected snake.
- Commands can be **replaced by sending another request before the tick ends**.

### Observability
- Visibility is **partial**.
- The world is divided into invisible sectors of size **30 pixels**.
- A player sees enemy snakes, obstacles and tangerines in the current sector and adjacent sectors, including diagonals.

### Collisions and reward
- Head collision with almost any non-food object destroys the snake.
- A snake can hit walls, obstacles, or other snakes.
- Respawn applies a **-10% score penalty**.
- Food value changes with map position and round progress.
- “Doubtful” food has hidden true reward at decision time.

## Engineering implications from the warm-up

1. Expect **server-authoritative JSON responses** with explicit time budget fields like `tickRemainMs`.
2. Expect that **invalid commands may be ignored rather than hard-failing the whole request**.
3. Expect that **command overwrite inside a tick may be legal**.
4. Expect **partial observability** or at least incomplete state in some Datsteam games.
5. Expect **non-trivial reward design**, including delayed or hidden reward components.
6. Expect that a local predictor / local state synchronizer can be useful between server updates.

## What not to overfit

Do not assume that DatsSol will also be:
- 3D,
- snake-based,
- single-endpoint,
- sector-visibility based,
- food-scoring based.

Use this only to infer **interaction style**, not final mechanics.

## Source notes

- Raw source in repo: `doc.pdf`
