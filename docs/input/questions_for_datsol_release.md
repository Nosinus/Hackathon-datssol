# Questions for the DatsSol release

This file lists what is still unknown and should remain isolated in the codebase until the real DatsSol rules are published.

## Must know before the first real run

1. What is the actual endpoint structure?
   - one endpoint or separate scan / command endpoints?
   - pull model or push model?

2. What authentication header is required?
   - `X-Auth-Token`, `X-API-Key`, or something else?

3. What is the time budget?
   - per tick?
   - per request?
   - what happens on late / invalid / missing requests?

4. What is the state/action schema?
   - exact JSON examples
   - required fields
   - optional fields
   - maximum payload sizes

5. Is the game simultaneous or sequential?
   - are all players resolved at once each tick?

6. What is the visibility model?
   - full state?
   - local visibility?
   - scanned visibility?
   - hidden information?

7. Are transitions deterministic?
   - randomness?
   - physics?
   - hidden state?
   - tie-breaking randomness?

8. What is the scoring function?
   - survival?
   - points?
   - placement?
   - private evaluation?
   - tie-break rules?

9. Are there rate limits or concurrency limits?

10. Is there a test / sandbox environment distinct from final rounds?

## Important for architecture but not required to start coding

11. Can commands be overwritten within the same tick?
12. Are logs or replays available from the organizer side?
13. Are there schedule / registration endpoints?
14. Can game constants differ between test and final?
15. Is there a static map download or map endpoint?
16. Are there explicit error codes and recovery rules?

## Critical policy / compliance questions

17. Are external LLM or cloud reasoning services allowed during live play?
18. Are locally hosted models allowed?
19. Is any human-in-the-loop intervention forbidden during rounds?
20. Are remote coding agents allowed during active rounds?
21. Are there restrictions on geographic hosting or outbound network use?
22. Is there a documented autonomy / fairness / anti-cheat policy?

## What the code should do until answers exist

- keep DatsSol behind interfaces and TODOs,
- document every assumption,
- prefer fixtures and generic abstractions,
- avoid embedding DatsBlack- or Snake-specific constants into the core.
