"""Deprecated placeholder module kept for backward compatibility.

DatsSol now has a concrete v1 adapter under `games.datssol`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatsSolContractPlaceholder:
    schema_status: str = "released_v1"
    notes: str = "Use games.datssol.models/raw+adapter+strategy instead of placeholder assumptions."
