from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from games.datsblack.models.raw import (
    LongScanResponse,
    MapResponse,
    RegistrationResponse,
    ScanResponse,
    ShipCommandResponse,
)

FIXTURES = Path("tests/fixtures/datsblack_lifecycle")


def _load(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_map_response_fixture() -> None:
    model = MapResponse.model_validate(_load("map_success.json"))
    assert model.success is True
    assert model.mapUrl == "https://example.test/map.png"


def test_registration_success_and_failure_fixtures() -> None:
    ok = RegistrationResponse.model_validate(_load("registration_success.json"))
    fail = RegistrationResponse.model_validate(_load("registration_failure.json"))
    assert ok.success is True
    assert fail.success is False
    assert fail.errors is not None


def test_longscan_success_and_failure_fixtures() -> None:
    ok = LongScanResponse.model_validate(_load("longscan_success.json"))
    fail = LongScanResponse.model_validate(_load("longscan_failure.json"))
    assert ok.success is True
    assert fail.success is False


def test_shipcommand_success_and_failure_fixtures() -> None:
    ok = ShipCommandResponse.model_validate(_load("shipcommand_success.json"))
    fail = ShipCommandResponse.model_validate(_load("shipcommand_failure.json"))
    assert ok.success is True
    assert fail.success is False


def test_scan_partial_unknown_fields_are_ignored() -> None:
    scan = ScanResponse.model_validate(_load("scan_partial_unknown.json"))
    assert scan.success is True
    assert scan.scan.tick == 44
    assert len(scan.scan.myShips) == 1


def test_scan_malformed_payload_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        ScanResponse.model_validate(_load("scan_malformed_missing_scan.json"))
