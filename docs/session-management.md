# APX Session Management

APX exposes one owner-facing flow while using separate internal Environment
identities:

```text
Boot -> Hub -> selected Environment -> Hub
```

This is the current concise contract. The former design/history is preserved at
`history/session-management-foundation-through-2026-09-01.md`; the complete
human-identity proposal remains in `human-identity-and-session-handoff-v1.md`.

## Current physical pilot

The experimental pilot boots into a supervised Hyprland/QuickShell Hub. It no
longer uses the historical concurrent SDDM/KDE Hub and Development sessions.
The Host owns transition/recovery machinery, while UI requests cross bounded
clients and executors. Only one normal graphical Environment is intended to be
active; the current handoff records which Environment was actually observed.

The tty recovery path remains independent of QuickShell and Hyprland. A broken
desktop must not remove the ability to observe or recover APX state.

## Authority

- Only the authenticated active Hub may request management operations such as
  switch, create, snapshot, archive, restore, force-stop or destroy.
- A workload may request graceful stop/return only for its own observed active
  generation.
- The Host executor independently validates the caller, active session,
  registration, generation, requested operation and current machine state.
- Hiding a UI action is not an authorization boundary.

## Handoff sequence

For Hub-to-Environment and Environment-to-Hub transitions, APX must:

1. bind the request to the authoritative active generation;
2. reject uncertain operations or conflicting graphical ownership;
3. stop/release session services and explicitly granted devices in order;
4. start the target under the supervised Host boundary;
5. verify runtime and graphical readiness, not merely process existence;
6. publish the new active-session evidence;
7. recover to the Hub or the independent recovery surface when a terminal gate
   cannot be established.

A blank display, a logout response or a changed process ID alone never proves a
successful handoff. The broker/executor journal owns the terminal result.

## Desktop behavior

Hyprland and QuickShell implement the current default presentation. Workload
menus expose return-to-Hub and read-only status; Hub menus expose management
actions allowed by the executor catalogue. Keyboard focus, outside dismissal
and pointer behavior are compositor-facing acceptance requirements and need
physical observation in addition to unit tests.

APX lifecycle remains desktop-independent. Future KDE, GNOME or other adapters
must implement the same release/readiness contract without becoming trusted
authority themselves.

## Process and service lifecycle

Environment processes and normal services exist only while their Environment is
active unless a future reviewed policy explicitly permits otherwise. Stop must
account for user processes, subordinate runtimes, namespaces, mounts, devices,
audio and local assistants. APX distinguishes clean stop, refusal due to active
work, failure, forced termination and recoverable incomplete handoff.

## Authentication still open

The pilot proves session orchestration, not the final human authentication
design. Secure automatic Hub entry, lock/unlock credential lifetime, recovery
credentials and future multi-person grouping remain open architecture work.
Internal Linux identities must stay hidden from the normal experience without
being treated as sufficient authentication or containment.

## Related evidence

- `general-graphical-handoff-and-host-controls-2026-08-03.md`
- `environment-handoff-runtime-readiness-fix-2026-08-18.md`
- `direct-hub-boot-v1-architecture-and-pending-result-2026-08-03.md`
- `graphical-hub-input-handoff-2026-07-19.md`
- `official-hub-health-watchdog-and-shell-stability-2026-08-02.md`
- `privileged-executor-protocol-v1.md`
