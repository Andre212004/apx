# Host Wi-Fi captive portal v1 — architecture and physical result

## Implemented boundary

The Host remains the sole Wi-Fi authority and the source of connectivity
classification. Host Shared Services v3 now adds, without removing existing
operations:

- `network.connectivity-check` and `network.portal.open`;
- `network.connectivity_changed`;
- `unknown`, `none`, `limited`, `portal`, and `full` state;
- an always-present structured `portal` object;
- v3 client commands `wifi-connectivity-check` and `wifi-portal-open`;
- Quickshell aggregate fields and explicit portal/recheck controls.

The check is bound to `wlan0`, requires a default route on that interface and
invalidates cached state on SSID/BSS change. It reads link-level RFC 8910
CAPPORT information exposed from DHCPv4, DHCPv6 or IPv6 Router Advertisements,
with raw DHCPv4 option 114 as a fallback, and accepts only an HTTPS API URI. RFC 8908
responses require `application/captive+json`, valid TLS, bounded content and
typed fields. The fallback is a bounded cleartext request to the Arch Linux
NetworkManager check endpoint; the expected body means `full`, a validated
redirect or intercepted HTML means `portal`, and transport/DNS failures remain
`limited` rather than being guessed as a portal. Response bodies, cookies,
credentials, query strings and fragments are never logged.

## Environment-only authentication window

The Host does not contain a browser and does not launch graphical processes.
For a detected portal it returns only its own in-memory validated URL to the
authenticated active Environment. The Hub adapter sends that URL over stdin —
never argv or environment — to `apx-captive-portal-browser-v1.py`.

The Hub contains WebKitGTK plus Python GObject, not a general browser. The APX
window has an ephemeral WebKit data manager and a private runtime directory;
it has no persistent history, profile, bookmarks, desktop entry or general
navigation control. Downloads, web permission requests, developer extras,
offline storage, page cache, non-HTTP(S) schemes and duplicate windows are
blocked. Normal portal redirects and same-window OAuth flows remain possible.
Closing the window deletes its runtime directory and asks the Host to check
connectivity again.

## Security and limitations

- DHCP/CAPPORT data are network-provided and not treated as owner input.
- CAPPORT TLS validation is never disabled; invalid CAPPORT falls back to the
  legacy HTTP probe as required by the standards.
- Portal URLs can legitimately contain per-client tokens. They remain in
  process memory and the authenticated socket response but never enter logs,
  notifications, argv, environment variables or temporary files.
- The WebKit window intentionally denies camera, microphone, location and file
  downloads. A portal that requires one of those capabilities will need a
  later explicit policy decision rather than silent access.
- Detection depends on the Arch connectivity endpoint. A later APX-operated
  endpoint could remove that external dependency, but it is not required for
  this bounded pilot.

## Evidence

The physical normal-network check returned `full` with no portal. A live Hub
window opened the neutral probe page under WebKit's network/web subprocesses,
used a mode-0700 runtime directory and removed it on exit. No Chromium,
Firefox, browser desktop entry or persistent profile exists. Focused tests
cover normal access, CAPPORT captive and non-captive states, redirect, HTML
interception, timeout, no route, false positive, unsafe scheme/userinfo, DHCP
option 114 and caller-supplied URL refusal. The installed systemd sandbox
passed a live `full` check with only `CAP_NET_RAW` and the bounded UNIX, INET,
INET6 and NETLINK address families.

The source, unit and Hub packages are installed and the new v3 daemon is active
and stable. Its restart also closed an older lifecycle mismatch: a socket leased
to the translated active-Hub UID is now accepted for safe retirement because
only root can replace entries in the root-owned `/run/apx` directory; symlinks
and non-sockets remain rejected. The currently running Hub still holds the old
file-bind inode. One Hub restart after closing the Host-console/Codex session
mounts the new socket; a Host reboot is not required.
