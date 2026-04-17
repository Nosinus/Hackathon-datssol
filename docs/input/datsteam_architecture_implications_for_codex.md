# Datsteam architecture implications for Codex

This file synthesizes the practical engineering implications across:

- DatsSol public event metadata,
- DatsBlack mechanics + OpenAPI,
- Snake3D warm-up,
- the research memo.

Its purpose is to convert “context” into a concrete overnight build plan.

## The recurring Datsteam pattern

Across the available materials, the safest shared pattern is:

1. a **server-authoritative** game server,
2. **tick-based** decision making,
3. **HTTP + JSON** interaction,
4. explicit **authentication header**,
5. partial or imperfect information is likely,
6. mechanics may differ between demo/test/final,
7. replayability and logging matter,
8. correctness and timing matter as much as strategy quality.

## What varies across Datsteam games

Do not hard-code any of these into the generic core:

- header name (`X-Auth-Token` vs `X-API-Key`)
- endpoint shape (single move endpoint vs scan + command split)
- dimensionality (3D snake vs 2D fleet)
- action structure
- scoring structure
- visibility model
- round registration flow
- response compression behavior
- tick duration

## Therefore the repo should be split into:

### 1. Generic competition core
Keep these game-agnostic:

- config
- environment loading
- auth abstraction
- HTTP transport
- retry / timeout / compression hooks
- structured logging
- replay writer
- canonical clock / tick metadata
- strategy interface
- budget manager
- deterministic fallback contract
- evaluator scaffold
- test utilities

### 2. Game adapter layer
Keep these per-game:

- raw schema models
- canonicalization
- legal action generation
- static map parsing
- domain-specific geometry
- baseline heuristics
- simulators / forward models

### 3. DatsBlack exemplar adapter
Implement this tonight because it is the richest available prior.

### 4. DatsSol placeholder adapter
Keep this as interfaces + TODOs until real rules arrive.

## What Codex should optimize for tonight

### Primary objective
Wake up to a repo that is:
- clean,
- typed,
- runnable locally,
- testable from fixtures,
- easy to retarget.

### Not the objective
- perfect strategy,
- final-tuned gameplay,
- deep search,
- cloud LLM orchestration inside runtime,
- live server validation.

## Recommended overnight task breakdown

### CONTRACT / DOCS
- summarize current truths,
- list DatsSol unknowns,
- document source priority,
- explain how DatsBlack is being used.

### CORE ENGINE
- config and env handling,
- transport,
- validation,
- replay / telemetry,
- canonical runtime interfaces.

### DATSBLACK ADAPTER
- raw models,
- canonical state builder,
- legal command builder,
- safe baseline,
- fixtures,
- tests.

### QUALITY / DEVEX
- README,
- quickstart,
- Makefile or task runner,
- lint / type / test commands,
- CI scaffold if lightweight,
- sample config and log paths.

## Key design guardrails

1. **No live LLM calls in the default move path.**
2. **Always preserve a deterministic fallback.**
3. **Never send unvalidated JSON.**
4. **Do not overfit the core to Snake3D or DatsBlack.**
5. **Do not block on missing DatsSol rules.**
6. **Use fixtures and offline tests because Codex does not have internet access here.**

## Concrete suggestion for repo shape

```text
repo/
  AGENTS.md
  README.md
  .env.example
  Makefile
  docs/
    input/
      ...offline context pack...
    contract/
    strategy/
    dev/
  src/
    datsteam_core/
      config/
      transport/
      auth/
      replay/
      runtime/
      evaluator/
      types/
    games/
      datsblack/
        api/
        models/
        canonical/
        strategy/
        fixtures/
      datssol/
        placeholders/
  tests/
  scripts/
```

## Why DatsBlack should be the exemplar

Because DatsBlack currently provides all three of these at once:

- real mechanics prose,
- a real OpenAPI document,
- a real action/state split.

That makes it ideal for proving the generic architecture without pretending the upcoming game is already known.

## Minimum acceptable morning result

If the repo has all of the following, the night run is a success:

- root docs make sense,
- generic core exists,
- DatsBlack adapter exists,
- a fixture-driven agent loop runs locally,
- deterministic fallback exists,
- tests cover non-trivial logic,
- DatsSol unknowns are isolated and documented.
