from __future__ import annotations

from typing import Any

import httpx
import pytest

from datsteam_core.transport.http import (
    HttpTransport,
    TransportJsonDecodeError,
    TransportNetworkError,
    TransportSchemaError,
)
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
        timeout: object | None = None,
    ) -> httpx.Response:
        _ = (method, path, headers, json, timeout)
        return self._response


class _NetworkErrorClient:
    def __enter__(self) -> _NetworkErrorClient:
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
        timeout: object | None = None,
    ) -> httpx.Response:
        _ = (method, path, headers, json, timeout)
        raise httpx.ConnectError("boom")


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
    with pytest.raises(TransportJsonDecodeError, match="JSON payload must be object"):
        transport.get_validated("/api/scan", ScanResponse)


def test_transport_raises_schema_error_on_malformed_object(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("GET", "https://example.test/api/scan")
    response = httpx.Response(200, json={"success": True}, request=request)
    _patch_client(monkeypatch, response)

    transport = HttpTransport(base_url="https://example.test", default_headers={})
    with pytest.raises(TransportSchemaError, match="Schema mismatch"):
        transport.get_validated("/api/scan", ScanResponse)


def test_transport_classifies_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "datsteam_core.transport.http.httpx.Client", lambda *a, **k: _NetworkErrorClient()
    )
    transport = HttpTransport(base_url="https://example.test", default_headers={})

    with pytest.raises(TransportNetworkError):
        transport.get_validated("/api/scan", ScanResponse)


def test_transport_captures_request_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("GET", "https://example.test/api/scan")
    response = httpx.Response(
        200,
        json={"scan": {"myShips": [], "enemyShips": [], "zone": None, "tick": 1}, "success": True},
        request=request,
        headers={"X-Trace-Id": "abc"},
    )
    _patch_client(monkeypatch, response)

    transport = HttpTransport(base_url="https://example.test", default_headers={})
    transport.get_validated("/api/scan", ScanResponse)

    assert transport.last_request_meta is not None
    assert transport.last_request_meta.path == "/api/scan"
    assert transport.last_request_meta.status_code == 200
    assert transport.last_request_meta.trace_id == "abc"


def test_transport_reuses_single_client(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("GET", "https://example.test/api/scan")
    response = httpx.Response(
        200,
        json={"scan": {"myShips": [], "enemyShips": [], "zone": None, "tick": 1}, "success": True},
        request=request,
    )
    calls = {"count": 0}

    def _factory(*args: Any, **kwargs: Any) -> _FakeClient:
        _ = (args, kwargs)
        calls["count"] += 1
        return _FakeClient(response)

    monkeypatch.setattr("datsteam_core.transport.http.httpx.Client", _factory)
    transport = HttpTransport(base_url="https://example.test", default_headers={})
    transport.get_validated("/api/scan", ScanResponse)
    transport.get_validated("/api/scan", ScanResponse)

    assert calls["count"] == 1


def test_transport_uses_longer_connect_timeout_for_gets(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("GET", "https://example.test/api/scan")
    response = httpx.Response(
        200,
        json={"scan": {"myShips": [], "enemyShips": [], "zone": None, "tick": 1}, "success": True},
        request=request,
    )
    captured: dict[str, object] = {}

    class _CapturingClient(_FakeClient):
        def request(
            self,
            method: str,
            path: str,
            *,
            headers: dict[str, str],
            json: dict[str, object] | None,
            timeout: object | None = None,
        ) -> httpx.Response:
            captured["method"] = method
            captured["timeout"] = timeout
            return super().request(method, path, headers=headers, json=json, timeout=timeout)

    monkeypatch.setattr(
        "datsteam_core.transport.http.httpx.Client",
        lambda *a, **k: _CapturingClient(response),
    )
    transport = HttpTransport(base_url="https://example.test", default_headers={}, timeout_seconds=5.0)
    transport.get_validated("/api/scan", ScanResponse, timeout_seconds=0.6)

    assert captured["method"] == "GET"
    assert isinstance(captured["timeout"], httpx.Timeout)
    assert captured["timeout"].connect == 5.0
    assert captured["timeout"].read == 0.6
