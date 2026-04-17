from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from datsteam_core.types.core import ActionEnvelope, CanonicalState


@dataclass(frozen=True)
class ReplayTickEnvelope:
    """Canonical per-tick replay record used by offline decision evaluation."""

    schema_version: str
    session_id: str
    round_id: str
    turn_id: int
    server_tick: int
    state_hash: str
    strategy_id: str
    action_reason: str
    request_payload: dict[str, Any]
    response_payload: dict[str, Any]
    canonical_state: dict[str, Any]
    chosen_action: dict[str, Any]
    validator_result: dict[str, bool] = field(default_factory=dict)
    request_meta: dict[str, Any] = field(default_factory=dict)
    response_meta: dict[str, Any] = field(default_factory=dict)
    transport_error: dict[str, Any] | None = None
    fallback_used: bool = False
    candidate_count: int = 0
    candidate_actions: list[dict[str, Any]] = field(default_factory=list)
    candidate_scores: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: int | None = None
    remaining_budget_ms: int | None = None
    fallback_flags: dict[str, bool] = field(default_factory=dict)
    validation_flags: dict[str, bool] = field(default_factory=dict)
    parser_extras: dict[str, Any] = field(default_factory=dict)
    run_metadata: dict[str, Any] = field(default_factory=dict)
    written_at_utc: str | None = None
    result_success: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "round_id": self.round_id,
            "turn_id": self.turn_id,
            "server_tick": self.server_tick,
            "state_hash": self.state_hash,
            "strategy_id": self.strategy_id,
            "action_reason": self.action_reason,
            "request_payload": self.request_payload,
            "response_payload": self.response_payload,
            "canonical_state": self.canonical_state,
            "chosen_action": self.chosen_action,
            "validator_result": self.validator_result,
            "request_meta": self.request_meta,
            "response_meta": self.response_meta,
            "transport_error": self.transport_error,
            "fallback_used": self.fallback_used,
            "candidate_count": self.candidate_count,
            "candidate_actions": self.candidate_actions,
            "candidate_scores": self.candidate_scores,
            "latency_ms": self.latency_ms,
            "remaining_budget_ms": self.remaining_budget_ms,
            "fallback_flags": self.fallback_flags,
            "validation_flags": self.validation_flags,
            "parser_extras": self.parser_extras,
            "run_metadata": self.run_metadata,
            "written_at_utc": self.written_at_utc,
            "result_success": self.result_success,
        }


def canonical_state_to_payload(state: CanonicalState) -> dict[str, Any]:
    return {
        "tick": state.tick,
        "me": [entity.__dict__ for entity in state.me],
        "enemies": [entity.__dict__ for entity in state.enemies],
        "metadata": state.metadata,
    }


def _state_hash(canonical_state: dict[str, Any]) -> str:
    encoded = json.dumps(canonical_state, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def from_runtime_step(
    *,
    session_id: str,
    round_id: str,
    state: CanonicalState,
    action: ActionEnvelope,
    result: dict[str, Any],
    request_payload: dict[str, Any] | None = None,
    strategy_id: str = "unknown_strategy",
    validator_result: dict[str, bool] | None = None,
    request_meta: dict[str, Any] | None = None,
    response_meta: dict[str, Any] | None = None,
    transport_error: dict[str, Any] | None = None,
    fallback_used: bool = False,
    candidate_count: int = 0,
    candidate_actions: list[dict[str, Any]] | None = None,
    candidate_scores: list[dict[str, Any]] | None = None,
    latency_ms: int | None = None,
    remaining_budget_ms: int | None = None,
    fallback_flags: dict[str, bool] | None = None,
    validation_flags: dict[str, bool] | None = None,
    parser_extras: dict[str, Any] | None = None,
    run_metadata: dict[str, Any] | None = None,
    written_at_utc: str | None = None,
) -> ReplayTickEnvelope:
    canonical_payload = canonical_state_to_payload(state)
    return ReplayTickEnvelope(
        schema_version="replay.v3",
        session_id=session_id,
        round_id=round_id,
        turn_id=state.tick,
        server_tick=state.tick,
        state_hash=_state_hash(canonical_payload),
        strategy_id=strategy_id,
        action_reason=action.reason,
        request_payload=request_payload or {},
        response_payload=result,
        canonical_state=canonical_payload,
        chosen_action={"payload": action.payload, "reason": action.reason},
        validator_result=validator_result or {},
        request_meta=request_meta or {},
        response_meta=response_meta or {},
        transport_error=transport_error,
        fallback_used=fallback_used,
        candidate_count=candidate_count,
        candidate_actions=candidate_actions or [],
        candidate_scores=candidate_scores or [],
        latency_ms=latency_ms,
        remaining_budget_ms=remaining_budget_ms,
        fallback_flags=fallback_flags or {},
        validation_flags=validation_flags or {},
        parser_extras=parser_extras or {},
        run_metadata=run_metadata or {},
        written_at_utc=written_at_utc,
        result_success=result.get("success") if isinstance(result.get("success"), bool) else None,
    )


def upgrade_legacy_record(payload: dict[str, Any]) -> ReplayTickEnvelope:
    tick = payload.get("tick", 0)
    state = payload.get("state")
    canonical_state = state if isinstance(state, dict) else {"tick": tick}
    action = payload.get("action")
    chosen_action = {
        "payload": action if isinstance(action, dict) else {},
        "reason": str(payload.get("reason", "legacy")),
    }
    result = payload.get("result")
    response_payload = result if isinstance(result, dict) else {}
    return ReplayTickEnvelope(
        schema_version="replay.v3",
        session_id=str(payload.get("session_id", "legacy-session")),
        round_id=str(payload.get("round_id", "legacy-round")),
        turn_id=int(tick) if isinstance(tick, int) else 0,
        server_tick=int(tick) if isinstance(tick, int) else 0,
        state_hash=_state_hash(canonical_state),
        strategy_id="legacy",
        action_reason=str(chosen_action["reason"]),
        request_payload={},
        response_payload=response_payload,
        canonical_state=canonical_state,
        chosen_action=chosen_action,
        validation_flags={"upgraded_from_legacy": True},
        run_metadata={},
        result_success=response_payload.get("success")
        if isinstance(response_payload.get("success"), bool)
        else None,
    )
