from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError


class TransportError(RuntimeError):
    pass


@dataclass
class HttpTransport:
    base_url: str
    default_headers: dict[str, str]
    timeout_seconds: float = 1.5

    def _request(
        self, method: str, path: str, body: dict[str, object] | None = None
    ) -> dict[str, Any]:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds) as client:
            response = client.request(method, path, headers=self.default_headers, json=body)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TransportError("JSON payload must be object")
        return payload

    def get_validated(self, path: str, model: type[BaseModel]) -> BaseModel:
        raw = self._request("GET", path)
        try:
            return model.model_validate(raw)
        except ValidationError as exc:
            raise TransportError(f"Schema mismatch for GET {path}: {exc}") from exc

    def post_validated(
        self,
        path: str,
        body: dict[str, object],
        model: type[BaseModel],
    ) -> BaseModel:
        raw = self._request("POST", path, body=body)
        try:
            return model.model_validate(raw)
        except ValidationError as exc:
            raise TransportError(f"Schema mismatch for POST {path}: {exc}") from exc
