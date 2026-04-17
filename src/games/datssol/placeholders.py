"""DatsSol adapter placeholder.

Unknowns intentionally isolated until official rules are released.
See docs/contract/open_questions.md and docs/contract/assumptions.md.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatsSolContractPlaceholder:
    schema_status: str = "unknown"
    notes: str = "Await official release; keep generic core and adapters decoupled."
