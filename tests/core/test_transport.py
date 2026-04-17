from __future__ import annotations

from typing import Any

import httpx
import pytest

from datsteam_core.transport.http import HttpTransport, TransportError, TransportSchemaError
from games.datsblack.models.raw import ScanResponse


class _FakeClient:
    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
        json: dict[str, object] | None,
    ) -> httpx.Response:
        _ = (method, path, headers, json)
        return self._response


def _patch_client(monkeypatch: pytest.MonkeyPatch, response: httpx.Response) -> None:
    def _factory(*args: Any, **kwargs: Any) -> _FakeClient:
        _ = (args, kwargs)
        return _FakeClient(response)

    monkeypatch.setattr("datsteam_core.transport.http.httpx.Client", _factory)


def test_transport_rejects_non_object_json(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("GET", "https://example.test/api/scan")
    response = httpx.Response(200, content=b"[]", request=request)
    _patch_client(monkeypatch, response)

    transport = HttpTransport(base_url="https://example.test", default_headers={})
    with pytest.raises(TransportError, match="JSON payload must be object"):
        transport.get_validated("/api/scan", ScanResponse)


def test_transport_raises_schema_error_on_malformed_object(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("GET", "https://example.test/api/scan")
    response = httpx.Response(200, json={"success": True}, request=request)
    _patch_client(monkeypatch, response)

    transport = HttpTransport(base_url="https://example.test", default_headers={})
    with pytest.raises(TransportSchemaError, match="Schema mismatch"):
        transport.get_validated("/api/scan", ScanResponse)
