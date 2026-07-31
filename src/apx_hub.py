"""Pure, non-mutating view model for the future APX Hub interface."""

from __future__ import annotations

from dataclasses import dataclass

from apx_environment import validate_logical_name


HUB_VIEW_SCHEMA_VERSION = 1
SYSTEM_STATES = ("ready", "busy", "incomplete", "unavailable")
ENVIRONMENT_STATES = ("inactive", "active", "incomplete", "unconfirmed", "cleaning")
ROLES = ("hub", "hub-graphical", "standard", "graphical-base", "development")
APPROVAL_CLASSES = ("none", "unlocked-session", "explicit-confirmation", "strong-confirmation")
READ_ONLY_ACTIONS = ("details", "retry-check", "cleanup-status", "system-details")


def _is_hub_role(role: str) -> bool:
    return role in {"hub", "hub-graphical"}


@dataclass(frozen=True)
class EnvironmentSummary:
    logical_name: str
    display_name: str
    role: str
    state: str
    security_profile: str
    template_name: str
    storage_summary: str
    cleanup_summary: str | None = None


@dataclass(frozen=True)
class TemplateSummary:
    template_id: str
    display_name: str
    description: str
    security_profile: str
    main_software: tuple[str, ...]
    storage_estimate: str
    admitted: bool
    compatibility: str


@dataclass(frozen=True)
class HubAction:
    action_id: str
    label: str
    enabled: bool
    explanation: str
    request_kind: str | None
    approval_class: str


@dataclass(frozen=True)
class EnvironmentCard:
    logical_name: str
    title: str
    subtitle: str
    state_label: str
    security_label: str
    storage_label: str
    actions: tuple[HubAction, ...]


@dataclass(frozen=True)
class TemplateCard:
    template_id: str
    title: str
    description: str
    security_label: str
    software_label: str
    storage_label: str
    action: HubAction


@dataclass(frozen=True)
class HubViewModel:
    schema_version: int
    title: str
    system_state: str
    system_message: str
    environment_cards: tuple[EnvironmentCard, ...]
    template_cards: tuple[TemplateCard, ...]
    global_actions: tuple[HubAction, ...]
    warnings: tuple[str, ...]


def _action(
    action_id: str,
    label: str,
    enabled: bool,
    explanation: str,
    request_kind: str | None,
    approval_class: str,
) -> HubAction:
    if approval_class not in APPROVAL_CLASSES:
        raise ValueError("unsupported Hub approval class")
    if enabled and request_kind is None and action_id not in READ_ONLY_ACTIONS:
        raise ValueError("enabled mutating Hub action requires a fixed request kind")
    return HubAction(
        action_id=action_id,
        label=label,
        enabled=enabled,
        explanation=explanation,
        request_kind=request_kind,
        approval_class=approval_class,
    )


def _validate_environment(summary: EnvironmentSummary) -> None:
    if validate_logical_name(summary.logical_name) is not None:
        raise ValueError("invalid Environment name in Hub input")
    if not summary.display_name or len(summary.display_name) > 80:
        raise ValueError("invalid Environment display name")
    if summary.role not in ROLES:
        raise ValueError("unsupported Environment role in Hub input")
    if summary.state not in ENVIRONMENT_STATES:
        raise ValueError("unsupported Environment state in Hub input")
    for value in (summary.security_profile, summary.template_name, summary.storage_summary):
        if not value or len(value) > 160 or any(not character.isprintable() for character in value):
            raise ValueError("invalid Environment summary text")
    if summary.state == "cleaning":
        if (
            not isinstance(summary.cleanup_summary, str)
            or not summary.cleanup_summary
            or len(summary.cleanup_summary) > 160
            or any(not character.isprintable() for character in summary.cleanup_summary)
        ):
            raise ValueError("cleaning Environment requires safe progress text")
    elif summary.cleanup_summary is not None:
        raise ValueError("cleanup progress is valid only while cleaning")


def _environment_actions(
    summary: EnvironmentSummary,
    *,
    system_state: str,
    hub_is_active: bool,
) -> tuple[HubAction, ...]:
    system_ready = system_state == "ready" and hub_is_active
    details = _action("details", "Ver detalhes", True, "Mostra informação sem fazer alterações.", None, "none")

    if summary.state == "cleaning":
        return (
            _action(
                "cleanup-status",
                "Ver limpeza",
                True,
                "Mostra os recursos e o espaço que ainda estão a ser libertados. Não força a eliminação.",
                None,
                "none",
            ),
            details,
        )

    if summary.state == "incomplete":
        return (
            _action(
                "recover",
                "Recuperar",
                system_ready,
                "Há uma operação incompleta. O APX precisa de verificar o que aconteceu antes de permitir outras ações.",
                "recover-complete" if system_ready else None,
                "explicit-confirmation" if system_ready else "none",
            ),
            details,
        )

    if summary.state == "unconfirmed":
        return (
            _action(
                "retry-check",
                "Verificar novamente",
                True,
                "O APX não conseguiu confirmar o estado. Esta verificação não altera dados.",
                None,
                "none",
            ),
            details,
        )

    if summary.state == "active":
        return (
            _action("open", "Já está aberto", False, "Este Environment já está ativo.", None, "none"),
            _action("snapshot", "Criar ponto de recuperação", False, "É necessário fechar o Environment primeiro.", None, "none"),
            _action("archive", "Arquivar", False, "É necessário fechar o Environment primeiro.", None, "none"),
            _action("destroy", "Apagar", False, "Um Environment ativo nunca pode ser apagado.", None, "none"),
            details,
        )

    if _is_hub_role(summary.role):
        return (
            _action("open", "Hub atual", False, "Já estás a utilizar o Hub.", None, "none"),
            _action("snapshot", "Criar ponto de recuperação", False, "O Hub teria de estar fechado e verificado primeiro.", None, "none"),
            _action("destroy", "Apagar", False, "O Hub ativo não pode ser apagado. É necessário um caminho de recuperação verificado.", None, "none"),
            details,
        )

    return (
        _action(
            "open",
            "Abrir",
            system_ready,
            "Fecha o Hub de forma controlada e abre este Environment." if system_ready else "O sistema ainda não está pronto para trocar de Environment.",
            "activate" if system_ready else None,
            "unlocked-session" if system_ready else "none",
        ),
        _action(
            "capabilities",
            "Gerir dispositivos",
            system_ready,
            "Escolhe acesso opcional a câmara, microfone, comandos ou armazenamento removível." if system_ready else "Aguarda até o sistema estar pronto.",
            "configure-capabilities" if system_ready else None,
            "explicit-confirmation" if system_ready else "none",
        ),
        _action(
            "snapshot",
            "Criar ponto de recuperação",
            system_ready,
            "Guarda uma cópia local do estado atual." if system_ready else "Aguarda até o sistema estar pronto.",
            "snapshot" if system_ready else None,
            "explicit-confirmation" if system_ready else "none",
        ),
        _action(
            "archive",
            "Arquivar",
            system_ready,
            "Cria uma cópia verificada que pode ser guardada por mais tempo." if system_ready else "Aguarda até o sistema estar pronto.",
            "archive" if system_ready else None,
            "explicit-confirmation" if system_ready else "none",
        ),
        _action(
            "destroy",
            "Apagar",
            system_ready,
            "No aviso seguinte escolhes preservar as cópias ou apagar completamente o Environment, snapshots e arquivos." if system_ready else "Não é possível apagar enquanto o sistema não estiver totalmente verificado.",
            "destroy" if system_ready else None,
            "strong-confirmation" if system_ready else "none",
        ),
        details,
    )


def _environment_card(
    summary: EnvironmentSummary,
    *,
    system_state: str,
    hub_is_active: bool,
) -> EnvironmentCard:
    labels = {
        "inactive": "Pronto para abrir",
        "active": "Aberto agora",
        "incomplete": "Precisa de recuperação",
        "unconfirmed": "Estado por confirmar",
        "cleaning": summary.cleanup_summary or "A limpar",
    }
    return EnvironmentCard(
        logical_name=summary.logical_name,
        title=summary.display_name,
        subtitle=f"Modelo: {summary.template_name}",
        state_label=labels[summary.state],
        security_label=f"Segurança: {summary.security_profile}",
        storage_label=summary.storage_summary,
        actions=_environment_actions(summary, system_state=system_state, hub_is_active=hub_is_active),
    )


def _validate_template(template: TemplateSummary) -> None:
    if not template.template_id or len(template.template_id) > 128:
        raise ValueError("invalid template identity")
    for value in (
        template.display_name,
        template.description,
        template.security_profile,
        template.storage_estimate,
        template.compatibility,
    ):
        if not value or len(value) > 500 or any(not character.isprintable() for character in value):
            raise ValueError("invalid template summary text")
    if len(template.main_software) > 20 or any(
        not value or len(value) > 80 for value in template.main_software
    ):
        raise ValueError("invalid template software summary")


def default_graphical_template_summaries() -> tuple[TemplateSummary, ...]:
    """Map the admitted graphical catalogue into safe Hub display summaries."""
    from apx_graphical_template import template_catalogue

    software = {
        "hyprland-base-v1": ("Hyprland", "Waybar", "Foot", "Fuzzel"),
        "hub-hyprland-v1": ("Hyprland", "Waybar", "APX Hub"),
    }
    return tuple(
        TemplateSummary(
            template.template_id,
            template.display_name,
            template.description,
            "Essencial privado",
            software[template.template_id],
            "Armazenamento flexível com reserva global protegida para o Host",
            True,
            "compatible",
        )
        for template in template_catalogue()
    )


def _template_card(
    template: TemplateSummary,
    *,
    system_ready: bool,
) -> TemplateCard:
    enabled = system_ready and template.admitted and template.compatibility == "compatible"
    if not template.admitted:
        explanation = "Este modelo ainda não foi aprovado para criar Environments."
    elif template.compatibility != "compatible":
        explanation = "Este modelo não é compatível com a configuração atual."
    elif not system_ready:
        explanation = "O sistema ainda não está pronto para criar um Environment."
    else:
        explanation = "Revê os programas, acessos e espaço antes de criar."
    return TemplateCard(
        template_id=template.template_id,
        title=template.display_name,
        description=template.description,
        security_label=f"Segurança: {template.security_profile}",
        software_label=", ".join(template.main_software) or "Sem aplicações adicionais",
        storage_label=template.storage_estimate,
        action=_action(
            "create",
            "Criar Environment",
            enabled,
            explanation,
            "create" if enabled else None,
            "explicit-confirmation" if enabled else "none",
        ),
    )


def build_hub_view(
    environments: tuple[EnvironmentSummary, ...],
    templates: tuple[TemplateSummary, ...],
    *,
    system_state: str,
) -> HubViewModel:
    if system_state not in SYSTEM_STATES:
        raise ValueError("unsupported Hub system state")
    for summary in environments:
        _validate_environment(summary)
    for template in templates:
        _validate_template(template)
    names = [summary.logical_name for summary in environments]
    if len(names) != len(set(names)):
        raise ValueError("duplicate Environment in Hub input")
    template_ids = [template.template_id for template in templates]
    if len(template_ids) != len(set(template_ids)):
        raise ValueError("duplicate template in Hub input")

    active = [summary for summary in environments if summary.state == "active"]
    active_hubs = [summary for summary in active if _is_hub_role(summary.role)]
    hub_is_active = len(active) == 1 and len(active_hubs) == 1
    warnings: list[str] = []
    effective_state = system_state
    if len(active) > 1:
        effective_state = "incomplete"
        warnings.append("Foi detetado mais do que um Environment ativo. Todas as alterações estão bloqueadas.")
    elif active and not active_hubs:
        effective_state = "incomplete"
        warnings.append("O Hub não pode gerir Environments enquanto outro Environment está ativo.")
    elif not active_hubs:
        effective_state = "incomplete"
        warnings.append("O Hub ativo não foi confirmado. As ações que alteram dados estão bloqueadas.")

    system_messages = {
        "ready": "Tudo pronto para gerir os teus Environments.",
        "busy": "Uma operação está em curso. Podes consultar detalhes, mas novas alterações estão bloqueadas.",
        "incomplete": "O APX precisa de recuperar ou confirmar o estado antes de continuar.",
        "unavailable": "Não foi possível confirmar o estado do sistema. Nenhuma alteração será feita.",
    }
    if system_state != "ready":
        warnings.append(system_messages[system_state])

    system_ready = effective_state == "ready" and hub_is_active
    environment_cards = tuple(
        _environment_card(summary, system_state=effective_state, hub_is_active=hub_is_active)
        for summary in sorted(environments, key=lambda item: (not _is_hub_role(item.role), item.display_name.casefold()))
    )
    template_cards = tuple(
        _template_card(template, system_ready=system_ready)
        for template in sorted(templates, key=lambda item: item.display_name.casefold())
    )
    global_actions = (
        _action(
            "restore",
            "Restaurar cópia",
            system_ready,
            "Cria um novo Environment a partir de uma cópia verificada." if system_ready else "O sistema precisa de estar pronto antes de restaurar.",
            "restore" if system_ready else None,
            "explicit-confirmation" if system_ready else "none",
        ),
        _action("system-details", "Estado do APX", True, "Mostra verificações sem alterar o sistema.", None, "none"),
    )
    return HubViewModel(
        schema_version=HUB_VIEW_SCHEMA_VERSION,
        title="Os teus Environments",
        system_state=effective_state,
        system_message=system_messages[effective_state],
        environment_cards=environment_cards,
        template_cards=template_cards,
        global_actions=global_actions,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def render_hub_text(view: HubViewModel) -> str:
    lines = [view.title, view.system_message]
    for warning in view.warnings:
        lines.append(f"Aviso: {warning}")
    for card in view.environment_cards:
        lines.append(f"Environment: {card.title} — {card.state_label}")
        for action in card.actions:
            state = "disponível" if action.enabled else "bloqueado"
            lines.append(f"  {action.label}: {state} — {action.explanation}")
    for card in view.template_cards:
        state = "disponível" if card.action.enabled else "bloqueado"
        lines.append(f"Modelo: {card.title} — {card.action.label}: {state}")
    return "\n".join(lines)
