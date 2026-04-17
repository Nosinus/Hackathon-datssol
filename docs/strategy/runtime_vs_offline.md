# Runtime vs Offline Responsibilities

## Runtime (must be deterministic and resilient)
- poll state via validated transport,
- convert raw payload to canonical state,
- choose baseline action,
- sanitize/validate action,
- submit action,
- write replay telemetry.

## Offline (iteration loop)
- parse replay logs,
- cluster failures,
- inspect invalid or low-value decisions,
- compare strategies on fixtures,
- add regression tests.

## Non-goal (current baseline)
- no live LLM/model dependency in move path.
