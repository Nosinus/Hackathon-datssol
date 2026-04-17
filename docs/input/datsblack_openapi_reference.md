# DatsBlack OpenAPI reference (condensed from `datsblack_openapi.json`)

This file is the text-first wire-contract summary.
When there is any conflict between this file and prose summaries, prefer the raw `datsblack_openapi.json`.

## Server

- OpenAPI version: `3.0.1`
- API title: `Геймтон DatsBlack`
- Base server URL in the spec: `https://datsblack.datsteam.dev`

## Authentication

All documented endpoints require header:

- `X-API-Key`

## Endpoints

| Method | Path | Purpose | Request schema | Response schema |
|---|---|---|---|---|
| `GET` | `/api/map` | Карта поля боя | `—` | `MapResponse` |
| `GET` | `/api/scan` | Сканирование вокруг своих кораблей | `—` | `ScanResponse` |
| `POST` | `/api/longScan` | Сканирование удалённой точки на карте | `LongScan` | `LongScanResponse` |
| `POST` | `/api/shipCommand` | Обработка команд контроля кораблей | `ShipsCommands` | `ShipCommandResponse` |
| `POST` | `/api/deathMatch/registration` | Регистрация на death match | `—` | `RegistrationResponse` |
| `POST` | `/api/deathMatch/exitBattle` | Выход из death match боя | `—` | `CommonResponse` |
| `POST` | `/api/royalBattle/registration` | Регистрация на королевскую битву | `—` | `CommonResponse` |

## Core request / response schemas

### `ShipsCommands`
| Field | Type / shape | Notes |
|---|---|---|
| `ships` | `array<ShipCommand>` | Команды для кораблей |

### `ShipCommand`
| Field | Type / shape | Notes |
|---|---|---|
| `id` | `integer` | id корабля; example=34 |
| `changeSpeed` | `integer` | Изменение скорости корабля; nullable; example=3 |
| `rotate` | `integer` | Поворот корабля. Допустимые значения -90 и 90; nullable; example=-90 |
| `cannonShoot` | `object:CannonShoot` | Координаты выстрела из пушки; nullable |

### `ScanResponse`
| Field | Type / shape | Notes |
|---|---|---|
| `scan` | `object:Scan` |  |
| `success` | `boolean` | Показатель успешности запроса |
| `errors` | `array<Error>` | Массив ошибок; nullable |

### `Scan`
| Field | Type / shape | Notes |
|---|---|---|
| `myShips` | `array<MyShip>` | Ваши корабли |
| `enemyShips` | `array<EnemyShip>` | Вражеские корабли |
| `zone` | `object:Zone` | Информация о зоне в королевской битве; nullable |
| `tick` | `integer` | Тик битвы; example=34 |

### `MyShip`
| Field | Type / shape | Notes |
|---|---|---|
| `id` | `integer` | example=56 |
| `x` | `integer` | example=20 |
| `y` | `integer` | example=30 |
| `size` | `integer` | example=3 |
| `hp` | `integer` | example=4 |
| `maxHp` | `integer` | example=5 |
| `direction` | `string` | Направление носа корабля |
| `speed` | `integer` | example=5 |
| `maxSpeed` | `integer` | example=15 |
| `minSpeed` | `integer` | example=-1 |
| `maxChangeSpeed` | `integer` | example=7 |
| `cannonCooldown` | `integer` | example=1 |
| `cannonCooldownLeft` | `integer` | example=1 |
| `cannonRadius` | `integer` | example=20 |
| `scanRadius` | `integer` | example=25 |
| `cannonShootSuccessCount` | `integer` | Количество успешных попаданий из пушки по другим кораблям; example=3 |

### `EnemyShip`
| Field | Type / shape | Notes |
|---|---|---|
| `x` | `integer` | example=40 |
| `y` | `integer` | example=45 |
| `hp` | `integer` | example=4 |
| `maxHp` | `integer` | example=4 |
| `size` | `integer` | example=4 |
| `direction` | `string` | Направление носа корабля |
| `speed` | `integer` | example=10 |

### `LongScan`
| Field | Type / shape | Notes |
|---|---|---|
| `x` | `integer` | example=50 |
| `y` | `integer` | example=90 |

### `LongScanResponse`
| Field | Type / shape | Notes |
|---|---|---|
| `tick` | `integer` | Тик битвы |
| `success` | `boolean` | Показатель успешности запроса |
| `errors` | `array<Error>` | Массив ошибок; nullable |

### `ShipCommandResponse`
| Field | Type / shape | Notes |
|---|---|---|
| `tick` | `integer` | Тик битвы |
| `success` | `boolean` | Показатель успешности запроса |
| `errors` | `array<Error>` | Массив ошибок; nullable |

### `Zone`
| Field | Type / shape | Notes |
|---|---|---|
| `x` | `integer` | example=40 |
| `y` | `integer` | example=45 |
| `radius` | `integer` | example=20 |

### `CannonShoot`
| Field | Type / shape | Notes |
|---|---|---|
| `x` | `integer` | example=30 |
| `y` | `integer` | example=34 |

## Immediate implementation notes for Codex

1. Build a typed client around:
   - `GET /api/map`
   - `GET /api/scan`
   - `POST /api/longScan`
   - `POST /api/shipCommand`

2. Treat registration endpoints as operational helpers:
   - `POST /api/deathMatch/registration`
   - `POST /api/deathMatch/exitBattle`
   - `POST /api/royalBattle/registration`

3. Keep **raw models** separate from **canonical models**.
   Suggested canonical entities:
   - `MyShipState`
   - `VisibleEnemyShip`
   - `ZoneState`
   - `MapStaticState`
   - `BattleTickState`

4. Because `direction` examples in the schema are textual compass values (`north/east/south/west`), canonicalization should normalize them into a stable internal enum.

5. The spec does not itself document all mechanics timing and scoring nuances.
   Pair this file with `datsblack_truth_table_and_mechanics.md`.

## Source notes

- Raw source in repo: `datsblack_openapi.json`
