from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

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


class TransportNetworkError(TransportError):
    """Network/connectivity error while calling remote endpoint."""


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


class TransportJsonDecodeError(TransportError):
    """Response body is not valid JSON object."""


@dataclass(frozen=True)
class RetryPolicy:
    retries: int = 1
    backoff_initial_seconds: float = 0.2
    backoff_multiplier: float = 2.0
    backoff_max_seconds: float = 2.0


@dataclass(frozen=True)
class RequestMeta:
    method: str
    path: str
    latency_ms: int
    attempt: int
    status_code: int | None
    request_id: str
    trace_id: str | None


@dataclass
class HttpTransport:
    base_url: str
    default_headers: dict[str, str]
    timeout_seconds: float = 1.5
    retry_policy: RetryPolicy = RetryPolicy()
    accept_gzip: bool = True
    default_send_margin_ms: int = 50

    last_request_meta: RequestMeta | None = None
    _client: httpx.Client | None = field(default=None, init=False, repr=False)

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds)
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        *,
        retryable: bool,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        request_headers = dict(self.default_headers)
        if self.accept_gzip:
            request_headers["Accept-Encoding"] = "gzip"

        request_id = request_headers.get("X-Request-Id") or uuid4().hex
        request_headers["X-Request-Id"] = request_id

        backoff = self.retry_policy.backoff_initial_seconds
        max_attempts = self.retry_policy.retries + 1 if retryable else 1
        last_error: TransportError | None = None

        for attempt in range(1, max_attempts + 1):
            start = time.perf_counter()
            try:
                response = self._get_client().request(
                    method,
                    path,
                    headers=request_headers,
                    json=body,
                    timeout=timeout_seconds or self.timeout_seconds,
                )
                latency_ms = int((time.perf_counter() - start) * 1000)
                self.last_request_meta = RequestMeta(
                    method=method,
                    path=path,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    status_code=response.status_code,
                    request_id=request_id,
                    trace_id=response.headers.get("X-Trace-Id") or response.headers.get("Trace-Id"),
                )

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

                payload = self._parse_json_object(
                    response, method=method, path=path, attempt=attempt
                )
                return payload
            except httpx.TimeoutException:
                last_error = TransportTimeoutError(
                    f"Timeout for {method} {path}",
                    method=method,
                    path=path,
                    attempt=attempt,
                )
            except httpx.NetworkError as exc:
                last_error = TransportNetworkError(
                    f"Network error for {method} {path}: {exc}",
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

    def _parse_json_object(
        self, response: httpx.Response, *, method: str, path: str, attempt: int
    ) -> dict[str, Any]:
        content = response.content

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise TransportJsonDecodeError(
                "Response body is not valid JSON",
                method=method,
                path=path,
                attempt=attempt,
            ) from exc

        if not isinstance(payload, dict):
            raise TransportJsonDecodeError(
                "JSON payload must be object",
                method=method,
                path=path,
                attempt=attempt,
            )
        return payload

    def get_validated(
        self,
        path: str,
        model: type[BaseModel],
        *,
        timeout_seconds: float | None = None,
    ) -> BaseModel:
        raw = self._request("GET", path, retryable=True, timeout_seconds=timeout_seconds)
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
        timeout_seconds: float | None = None,
    ) -> BaseModel:
        raw = self._request(
            "POST",
            path,
            body=body,
            retryable=retryable,
            timeout_seconds=timeout_seconds,
        )
        try:
            return model.model_validate(raw)
        except ValidationError as exc:
            raise TransportSchemaError(
                f"Schema mismatch for POST {path}: {exc}",
                method="POST",
                path=path,
                attempt=1,
            ) from exc
