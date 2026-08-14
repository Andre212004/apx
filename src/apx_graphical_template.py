"""Pure catalogue and creation contract for APX Hyprland Environments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

from apx_environment import validate_logical_name


SCHEMA_VERSION = 2
BASE_RELEASE = "hyprland-base-v2"
CONFIG_SEED = "hyprland-minimal-v2"
DESKTOP_PROFILE = "desktop-essential-v1"
POLICY = "normal-desktop"
ESSENTIAL_CAPABILITIES = (
    "amd-graphics-mediated",
    "audio-mediated",
    "display-mediated",
    "host-mediated-outbound-network",
    "keyboard-mediated",
    "notifications-mediated",
    "portal-mediated",
    "touchpad-mediated",
)
OPTIONAL_CAPABILITIES = (
    "camera-mediated",
    "controller-mediated",
    "microphone-mediated",
    "removable-storage-mediated",
)
LOCAL_PACKAGE_ADMIN = "environment-local-sudo-pacman-unrestricted"
CONFIG_INHERITANCE = "copy-on-create-independent"
STORAGE_POLICY = "bounded-environment-with-protected-host-reserve"
ROOT_STORAGE_LIMIT = "32G"
HOME_STORAGE_LIMIT = "64G"


class GraphicalTemplateError(ValueError):
    pass


@dataclass(frozen=True)
class GraphicalTemplate:
    template_id: str
    role: str
    release: str
    config_seed: str
    desktop_profile: str
    display_name: str
    description: str
    essential_capabilities: tuple[str, ...]
    optional_capabilities: tuple[str, ...]
    default_optional_capabilities: tuple[str, ...]
    local_package_admin: str
    config_inheritance: str
    storage_policy: str
    hub_client: bool
    apx_session_control: bool
    gtk_management_app: bool
    waybar_apx_control: bool


@dataclass(frozen=True)
class GraphicalCreationPlan:
    schema_version: int
    logical_name: str
    template_id: str
    role: str
    release: str
    policy: str
    config_seed: str
    desktop_profile: str
    config_destination: str
    root_storage: str
    home_storage: str
    root_storage_limit: str
    home_storage_limit: str
    storage_policy: str
    capabilities: tuple[str, ...]
    local_package_admin: str
    effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    plan_digest: str


def _template(*, template_id: str, role: str, display_name: str,
              description: str, hub: bool) -> GraphicalTemplate:
    return GraphicalTemplate(
        template_id=template_id,
        role=role,
        release=BASE_RELEASE,
        config_seed=CONFIG_SEED,
        desktop_profile=DESKTOP_PROFILE,
        display_name=display_name,
        description=description,
        essential_capabilities=ESSENTIAL_CAPABILITIES,
        optional_capabilities=OPTIONAL_CAPABILITIES,
        default_optional_capabilities=(),
        local_package_admin=LOCAL_PACKAGE_ADMIN,
        config_inheritance=CONFIG_INHERITANCE,
        storage_policy=STORAGE_POLICY,
        hub_client=hub,
        apx_session_control=True,
        gtk_management_app=hub,
        waybar_apx_control=True,
    )


TEMPLATES = {
    "hyprland-base-v2": _template(
        template_id="hyprland-base-v2", role="graphical-base",
        display_name="Hyprland Base",
        description="Arch e Hyprland mínimos, funcionais e independentes.",
        hub=False,
    ),
    "hub-hyprland-v2": _template(
        template_id="hub-hyprland-v2", role="hub-graphical",
        display_name="APX Hub",
        description="Hub Hyprland mínimo com Waybar e gestão APX nativa.",
        hub=True,
    ),
}


def template_catalogue() -> tuple[GraphicalTemplate, ...]:
    return tuple(TEMPLATES[key] for key in sorted(TEMPLATES))


def build_creation_plan(logical_name: str, template_id: str) -> GraphicalCreationPlan:
    if validate_logical_name(logical_name) is not None:
        raise GraphicalTemplateError("invalid Environment logical name")
    try:
        template = TEMPLATES[template_id]
    except KeyError as error:
        raise GraphicalTemplateError("template is not admitted") from error
    if logical_name == "hub" and template.role != "hub-graphical":
        raise GraphicalTemplateError("the Hub requires the fixed graphical Hub template")
    if logical_name != "hub" and template.role == "hub-graphical":
        raise GraphicalTemplateError("the graphical Hub template is reserved for the Hub")

    root = f"/var/lib/apx/environments/{logical_name}/root"
    home = f"/var/lib/apx/environments/{logical_name}/home"
    draft = {
        "schema_version": SCHEMA_VERSION,
        "logical_name": logical_name,
        "template_id": template.template_id,
        "role": template.role,
        "release": template.release,
        "policy": POLICY,
        "config_seed": template.config_seed,
        "desktop_profile": template.desktop_profile,
        "config_destination": f"{home}/apx/.config",
        "root_storage": root,
        "home_storage": home,
        "root_storage_limit": ROOT_STORAGE_LIMIT,
        "home_storage_limit": HOME_STORAGE_LIMIT,
        "storage_policy": template.storage_policy,
        "capabilities": template.essential_capabilities,
        "local_package_admin": template.local_package_admin,
        "effects": (
            "snapshot-immutable-graphical-release-to-independent-writable-root",
            "create-independent-home-subvolume-with-role-size-cap",
            "apply-root-and-home-qgroup-limits",
            "verify-shared-pool-host-reserve-before-creation",
            "copy-versioned-config-seed-once",
            "create-environment-local-admin-account",
            "apply-essential-mediated-capability-profile",
            "publish-registration-only-after-isolation-verification",
        ),
        "forbidden_effects": (
            "activate-graphical-session",
            "copy-live-hub-or-environment-state",
            "grant-optional-devices-by-default",
            "modify-host-package-state",
            "share-writable-config-or-package-root",
        ),
    }
    digest = hashlib.sha256(
        json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return GraphicalCreationPlan(**draft, plan_digest=digest)


def canonical_template_json(template: GraphicalTemplate) -> str:
    if template not in TEMPLATES.values():
        raise GraphicalTemplateError("template differs from the admitted catalogue")
    return json.dumps(asdict(template), sort_keys=True, separators=(",", ":")) + "\n"
