"""Production authority composition for the local typed executor."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Callable

from apx_executor_contract import ExecutorRequest, OperationPlan
from apx_executor_endpoint import (
    AuthoritativeRequestState, EffectResult, EndpointAuthorities,
)
from apx_executor_peer import PeerCredentials, observe_peer
import apx_executor_store as store


ENVIRONMENTS = Path("/var/lib/apx/environments")
EffectAdapter = Callable[[OperationPlan, str], EffectResult]


class ExecutorAuthoritiesError(RuntimeError):
    pass


def build_authorities(credentials: PeerCredentials,
                      effect_adapter: EffectAdapter) -> EndpointAuthorities:
    if not callable(effect_adapter):
        raise ExecutorAuthoritiesError("typed effect adapter is unavailable")
    requester = observe_peer(credentials)

    def observe_state(request: ExecutorRequest) -> AuthoritativeRequestState:
        try:
            registration = json.loads(
                (ENVIRONMENTS / request.logical_name / "registration.json").read_text()
            )
        except (OSError, json.JSONDecodeError) as error:
            raise ExecutorAuthoritiesError("target registration is unavailable") from error
        if registration.get("name") != request.logical_name or registration.get("generation") != request.expected_generation:
            raise ExecutorAuthoritiesError("target registration identity differs")
        if registration.get("state") not in {"stopped", "running"}:
            raise ExecutorAuthoritiesError("target registration state differs")
        nonce_path = store.STORE_ROOT / "nonces" / request.nonce
        return AuthoritativeRequestState(
            registration["generation"], int(time.time()), requester.session_id,
            "used" if nonce_path.exists() else "unused",
            "confirmed-compatible", requester,
        )

    return EndpointAuthorities(
        store.load_plan, store.load_approval, observe_state,
        store.reserve_nonce, effect_adapter,
    )
