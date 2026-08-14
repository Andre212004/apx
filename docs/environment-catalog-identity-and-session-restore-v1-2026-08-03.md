# APX Environment catalog, identity and session restore v1 — 2026-08-03

## Installed catalog and identity boundary

The Host now owns the authoritative graphical Environment catalog.  The
authenticated Hub can request up to 64 trusted root-owned registrations and
receives only presentation/lifecycle fields: name, display name, category,
role, release, generation, state, update policy and the future session-restore
preference.  Invalid, untrusted and non-graphical registrations are omitted.

The Hub switch request now includes one validated target from that catalog;
the Host reopens and revalidates the registration and requires it to be stopped
before starting the existing supervised handoff.  The previous hard-coded
`hub-ficticio` target is removed from the service, client and runner.  This does
not grant generic lifecycle authority: creation, deletion, snapshots, updates
and Host controls remain separate Hub-only contracts.

Every active graphical Environment can request only its own Host-authenticated
identity.  Workload UI shows that identity instead of a locally invented name.
A workload cannot request the catalog or select another workload.  Its only
exit path ends its own compositor; the Host supervisor revokes it, recovers
tty1 and returns to the Hub.  It cannot return to a Host shell or switch
directly to a sibling Environment.

Optional registration fields are `display_name` (1–64 characters), `category`
(a bounded lowercase identifier) and `session_restore` (strict boolean).  Old
registrations remain compatible and appear with a title-cased name, category
`general` and restore disabled.

## Requested session-restore behavior

Session restore is an accepted product direction but is not yet implemented or
physically certified.  It is per Environment, disabled by default, and the
toggle remains enabled across future entries until the owner disables it.
When enabled, leaving an Environment asks whether to save the current supported
application session.  Declining affects only that exit and does not disable the
persistent preference.

The save operation must create an Environment-local, user-owned manifest with
an atomic replace and strict size/count bounds.  It may contain application
identifiers, workspace placement and application-defined restore references;
it must not contain browser cookies, document contents, passwords, command
lines, environment variables or Host paths.  The manifest never crosses into
another Environment and disappears if that Environment is deleted.

Restoration is adapter-based rather than a generic process checkpoint:

- browsers use their own profile/session-restore facility and may restore tabs
  according to the browser's privacy/settings policy;
- LibreOffice reopens explicitly recorded Environment-local document paths and
  relies on its own recovery for unsaved content;
- unsupported applications are reported as not restorable and are closed
  normally;
- a crashed or incompatible restore never blocks entry; APX records a bounded
  local failure and starts a clean desktop.

CRIU-style freezing of an arbitrary Wayland/PipeWire/D-Bus process tree is not
adopted.  It is not a reliable substitute for application-level save/restore
and would create unsafe coupling to stale display, audio and credential state.

## Implementation order still required

1. Define and test the Environment-local manifest and persistent toggle.
2. Add read-only application discovery plus browser and LibreOffice adapters.
3. Add the exit prompt to both Hub-to-workload and workload-to-Hub UI paths.
4. Restore only after the new Environment session, D-Bus and compositor are
   ready, with duplicate-launch prevention.
5. Physically prove save, decline, restore, toggle persistence, missing files,
   application upgrade and failed-restore fallback in two Environments.

Until those steps pass, the catalog truthfully exposes `session_restore=false`
unless a registration was explicitly prepared for later development; no UI may
claim that running applications were saved.
