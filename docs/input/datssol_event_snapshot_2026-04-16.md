# DatsSol public event snapshot (captured 2026-04-16)

This file is **not** the final gameplay documentation.
It captures the currently visible public event metadata and the small amount of pre-start gameplay framing available before the real rules drop.

## What is publicly visible right now

A public DatsSol event listing mirrors the organizer text and says:

- DatsSol is a gamethon where you write an algorithm, send HTTP requests with JSON, receive a response, improve the strategy, and repeat.
- Teams: **1–3 people**
- Format: **online**
- Participation: **free**
- Age: **18+**
- Documentation: **released 1 hour before the start**
- Warm-up recommendation: **practice on Snake3D first**
- Schedule shown there:
  - 17 April, 18:00 UTC+3 — documentation
  - 17 April, 19:00 UTC+3 — training starts
  - 17 April, 22:00 UTC+3 — pause
  - 18 April — continuation + finals
  - 18 April, 18:00 UTC+3 — stream
  - 18 April, 20:00 UTC+3 — winners announced

A DevTeam Games event listing also places DatsSol in the same recurring Datsteam family as Snake3D, DatsNewWay, DatsBlack and other gamethons.

## What this means technically

Publicly visible DatsSol metadata supports only these **safe conclusions**:

1. The competition is still based on a **server-authoritative HTTP/JSON loop**.
2. The exact mechanics and contract are **not yet public in the repo**.
3. Snake3D is an **official warm-up prior** and therefore useful for studying organizer patterns.
4. DatsBlack is a **recommended previous championship** and therefore the best detailed exemplar available right now.

## What is still unknown

The public event copy does **not** yet answer:

- the actual state/action schema,
- endpoint structure,
- tick budget / timeout semantics,
- scoring,
- whether the game is simultaneous or sequential,
- visibility model,
- randomness / hidden state,
- live AI / autonomy rules,
- rate limits,
- test vs prod split,
- public vs private evaluation.

## How Codex should use this file

Use this file only for:

- event timing context,
- confidence that the final loop is HTTP/JSON based,
- confidence that the repo should stay generic and adaptable.

Do **not** use this file as proof of a Snake-like or DatsBlack-like final schema.

## Source notes

- Public event mirror: `https://www.xn--80aa3anexr8c.xn--p1acf/new/tpost/bcrms5i891-datssol`
- Event catalog: `https://devteam.games/events?id=019a7c9d-20a5-7c50-8d28-4914e8205b75`
