from __future__ import annotations

import gzip
import json
import time
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError


class TransportError(RuntimeError):
    """Base transport error with context for logs/metrics."""

    def __init__(self, message: str, *, method: str, path: str, attempt: int) -> None:
        super().__init__(message)
        self.method = method
        self.path = path
        self.attempt = attempt


class TransportTimeoutError(TransportError):
    """Timeout while calling remote endpoint."""


class TransportHttpStatusError(TransportError):
    """Remote endpoint returned non-2xx status code."""

    def __init__(
        self,
        message: str,
        *,
        method: str,
        path: str,
        attempt: int,
        status_code: int,
        response_text: str,
    ) -> None:
        super().__init__(message, method=method, path=path, attempt=attempt)
        self.status_code = status_code
        self.response_text = response_text


class TransportSchemaError(TransportError):
    """Response JSON did not match model schema."""


@dataclass(frozen=True)
class RetryPolicy:
    retries: int = 1
    backoff_initial_seconds: float = 0.2
    backoff_multiplier: float = 2.0
    backoff_max_seconds: float = 2.0


@dataclass
class HttpTransport:
    base_url: str
    default_headers: dict[str, str]
    timeout_seconds: float = 1.5
    retry_policy: RetryPolicy = RetryPolicy()
    accept_gzip: bool = True

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        *,
        retryable: bool,
    ) -> dict[str, Any]:
        request_headers = dict(self.default_headers)
        if self.accept_gzip:
            request_headers["Accept-Encoding"] = "gzip"

        backoff = self.retry_policy.backoff_initial_seconds
        max_attempts = self.retry_policy.retries + 1 if retryable else 1
        last_error: TransportError | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                with httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds) as client:
                    response = client.request(method, path, headers=request_headers, json=body)

                if response.status_code >= 500 and retryable and attempt < max_attempts:
                    time.sleep(backoff)
                    backoff = min(
                        backoff * self.retry_policy.backoff_multiplier,
                        self.retry_policy.backoff_max_seconds,
                    )
                    continue

                if response.status_code >= 400:
                    raise TransportHttpStatusError(
                        f"HTTP {response.status_code} for {method} {path}",
                        method=method,
                        path=path,
                        attempt=attempt,
                        status_code=response.status_code,
                        response_text=response.text[:300],
                    )

                payload = self._parse_json_object(response)
                return payload
            except httpx.TimeoutException:
                last_error = TransportTimeoutError(
                    f"Timeout for {method} {path}",
                    method=method,
                    path=path,
                    attempt=attempt,
                )
            except httpx.HTTPError as exc:
                last_error = TransportError(
                    f"HTTP client error for {method} {path}: {exc}",
                    method=method,
                    path=path,
                    attempt=attempt,
                )
            except TransportError as exc:
                last_error = exc

            if not retryable or attempt >= max_attempts:
                if last_error is None:
                    raise TransportError(
                        f"Unknown transport failure for {method} {path}",
                        method=method,
                        path=path,
                        attempt=attempt,
                    )
                raise last_error

            time.sleep(backoff)
            backoff = min(
                backoff * self.retry_policy.backoff_multiplier,
                self.retry_policy.backoff_max_seconds,
            )

        raise RuntimeError("unreachable")

    def _parse_json_object(self, response: httpx.Response) -> dict[str, Any]:
        content = response.content
        encoding = response.headers.get("Content-Encoding", "").lower()
        if encoding == "gzip":
            content = gzip.decompress(content)

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise TransportError(
                "Response body is not valid JSON",
                method=response.request.method,
                path=response.request.url.path,
                attempt=1,
            ) from exc

        if not isinstance(payload, dict):
            raise TransportError(
                "JSON payload must be object",
                method=response.request.method,
                path=response.request.url.path,
                attempt=1,
            )
        return payload

    def get_validated(self, path: str, model: type[BaseModel]) -> BaseModel:
        raw = self._request("GET", path, retryable=True)
        try:
            return model.model_validate(raw)
        except ValidationError as exc:
            raise TransportSchemaError(
                f"Schema mismatch for GET {path}: {exc}",
                method="GET",
                path=path,
                attempt=1,
            ) from exc

    def post_validated(
        self,
        path: str,
        body: dict[str, object],
        model: type[BaseModel],
        *,
        retryable: bool = False,
    ) -> BaseModel:
        raw = self._request("POST", path, body=body, retryable=retryable)
        try:
            return model.model_validate(raw)
        except ValidationError as exc:
            raise TransportSchemaError(
                f"Schema mismatch for POST {path}: {exc}",
                method="POST",
                path=path,
                attempt=1,
            ) from exc
