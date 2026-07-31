"""Pure role-aware APX button model for Hub and workload sessions."""

from __future__ import annotations

from dataclasses import dataclass

HUB_ROLES = ("hub", "hub-graphical")
WORKLOAD_ROLES = ("standard", "graphical-base", "development")
ROLES = HUB_ROLES + WORKLOAD_ROLES


@dataclass(frozen=True)
class SessionAction:
    action_id: str
    label: str
    mutates_environments: bool


@dataclass(frozen=True)
class SessionControlModel:
    role: str
    title: str
    management_enabled: bool
    actions: tuple[SessionAction, ...]


def build_session_control(role: str) -> SessionControlModel:
    """Return display affordances only; executor authorization remains decisive."""
    if role not in ROLES:
        raise ValueError("unsupported active Environment role")
    if role in HUB_ROLES:
        return SessionControlModel(
            role, "Centro APX", True,
            (
                SessionAction("switch", "Abrir Environment", False),
                SessionAction("create", "Criar Environment", True),
                SessionAction("configure-capabilities", "Gerir dispositivos", True),
                SessionAction("snapshot", "Criar ponto de recuperação", True),
                SessionAction("archive", "Arquivar Environment", True),
                SessionAction("restore", "Restaurar Environment", True),
                SessionAction("destroy", "Apagar Environment", True),
                SessionAction("details", "Ver estado do sistema", False),
            ),
        )
    return SessionControlModel(
        role, "APX", False,
        (
            SessionAction("return-to-hub", "Voltar ao HUB", False),
            SessionAction("current-details", "Ver este Environment", False),
            SessionAction("system-status", "Ver estado do APX", False),
        ),
    )
