from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeaderTokenAuth:
    header_name: str
    token: str

    def headers(self) -> dict[str, str]:
        return {self.header_name: self.token}
