# APX Testing Strategy v1

Status: staged test proposal; only repository-level tests are currently
authorized and running.

## Plain-Language Summary

APX will become testable gradually. We will not move directly from documents to
changing the real computer.

Each level answers a different question:

1. Do the rules reject unsafe requests?
2. Can disposable fake data exercise failures safely?
3. Can one empty experimental Environment run without touching personal data?
4. Can two Environments prove separation from each other?
5. Can graphical use, applications, hardware, and switching work safely?
6. Can APX recover after crashes and deliberate attacks?

Passing one level does not automatically authorize the next.

For the preferred clean-install route, the delivery gates are C0–C9 from
`headless-bootstrap-and-cli-first-v1.md`. C0–C6 prove bootstrap, the headless
Hub and Development Environment, package separation, lifecycle, storage,
recovery, and ordinary CLI use before any graphical component is installed.
H0 is then the first physical graphical gate. The older G2 campaign remains a
separate compatibility test for migrating the current KDE/SDDM machine; it is
not a prerequisite for the clean-install route.

## Level 1: Repository Contracts

Status: active today.

These tests run only against code and fake evidence inside the repository. They
do not create users, storage, containers, sessions, services, or packages.

Current coverage includes:

- names, registrations, creation and removal plans;
- read-only host and session observations;
- snapshot evidence and Stage 2 review plans;
- fixed normal and high-security isolation-policy contracts;
- fixed Hub operation plans and approval binding;
- rejection of commands, paths, unknown fields, stale generations, expired
  confirmations, reused nonces, wrong sessions, and changed plans.

Exit requirement: all tests pass deterministically and every new privileged
effect first has a pure contract and negative tests.

## Level 2: Disposable Filesystem Fixtures

Status: not started.

Tests use repository-owned temporary fixtures or an explicitly approved
disposable test area. They model files, journals, manifests, interrupted writes,
and corrupt records without representing them as real host resources.

Required scenarios include:

- crash before and after every journal step;
- duplicate, missing, oversized, and corrupted metadata;
- path replacement and symbolic-link attacks;
- fake storage identity reuse;
- quota and capacity evidence becoming unavailable;
- approval replay and clock rollback;
- recovery preserving uncertain data.

Exit requirement: no test can delete or adopt a fixture without exact recorded
identity and ownership evidence.

## Level 3: One Headless Experimental Environment

Status: designed but not authorized.

This is the first level that changes host state. It requires a separate preview
and explicit approval. The fixed `isolation-trial` identity is used, with no
desktop, GPU, audio, camera, microphone, input devices, personal data, Hub,
Odysseus, or Codex.

The test proves:

- isolated root and home creation;
- independent package database;
- local `sudo pacman` cannot change host packages;
- private processes, mounts, users, IPC, and network;
- enforced CPU, memory, process, and storage limits;
- complete stop and cleanup evidence;
- safe refusal when any identity is uncertain.

Before starting, APX must show exact downloads, storage, accounts, processes,
network effects, rollback limits, and cleanup plan.

Exit requirement: repeated create, boot, local package change, stop, restart,
and separately approved cleanup complete without host or unrelated changes.

## Level 4: Two-Environment Separation

Status: not designed in executable form.

Two disposable Environments install the same harmless package independently.
Tests then attempt, from normal user and local root, to access the other
Environment and the host.

Required denials include:

- files and package databases;
- processes, IPC, sockets, D-Bus, and services;
- mounts, snapshots, metadata, and operation records;
- network identity and undeclared host services;
- devices, secrets, clipboard, and portals;
- CPU, memory, process, and storage-limit removal;
- surviving processes after stop.

Deleting one Environment must leave the other byte-for-byte and semantically
unchanged where the measurement is meaningful.

Exit requirement: every attempted crossing is denied or the architecture is
stopped and revised. “Mostly isolated” is not accepted.

## Level 5: Graphical and Daily-Use Tests

Status: exact first Hyprland role resolved, built, finalized, and promoted into
the immutable `hyprland-h0-v1` release. Repository lifecycle support now admits
creation of a stopped `graphical-h0` Environment but deliberately refuses its
generic start. The runtime is now installed and the real stopped
`codex-test-hyprland-h0-v1` Environment exists. Its exact pure lease plan limits
H0 to AMD card2/renderD129, stable built-in keyboard/touchpad identities, tty2,
and a 120-second Host watchdog while preserving tty1. The minimal config passed
Hyprland's own parser inside the Environment with no device grant. The physical
compositor has still not started. G0 completed as a bounded negative result, G1
passed nested rendering, and G2 has a design contract but no executable preview
or authorization. This evidence is reusable, but the preferred clean-install
route reaches physical graphics through H0 only after C0–C6 pass.

Only after headless separation works do we add, one at a time:

- minimal Wayland display;
- mediated input;
- audio;
- notifications and file portal;
- clipboard and secret storage;
- removable storage;
- AMD graphics;
- NVIDIA graphics;
- Hyprland, KDE Plasma, and GNOME;
- Hub-to-Environment and return flow.

Each addition repeats separation and teardown tests. If a feature needs broad
host access, it remains disabled until a narrower design exists.

Exit requirement: the owner can use and switch Environments without seeing
internal Linux accounts, leaking data, leaving background runtimes, or losing a
recovery route to the Hub.

The first closure uses 194 new packages and is bound to manifest digest
`e2f6adfc19e00dfe7cae21b4eab1650437edf24d817dc355a9af449d1cd9b25e`.
G0 uses only the AMD render node and a headless Hyprland output; G1 adds a
mediated nested window while KDE remains available; G2 alone may request an
exclusive physical session. NVIDIA, raw input, audio, host Wayland/PipeWire/
D-Bus/portal sockets, and host home remain denied until their named stage.
The separately authorized graphical acquisition published exactly 194 packages
and 194 signatures totaling 264,707,836 bytes. Independent reopen matched every
package hash/size and found zero missing, unexpected, or partial files. Signer
trust and the independent cryptographic pass remain required.
Graphical signature verification then passed all 194 packages twice with 25
trusted primary identities. A regression fixture distinguishes an unrelated
expired historical subkey warning from `EXPKEYSIG`: only the former may coexist
with a valid current signer; expired signing keys remain blocked.
Bounded graphical metadata inspection matched all 194 inside-package identities
to the signed manifest and reproduced 1,022,339,199 declared installed bytes.
No other package member was extracted or executed.
The separately authorized offline role build produced a stopped 332-package
root at `/tmp/apx-hyprland-build-v1`, using 1,739,587,584 allocated bytes under
its 3 GiB limit. The 138-package source base remained content-identical, and an
independent read confirmed the internal package count, key executables, and
report digest. No compositor, hardware, audio, input, network, or host-session
access occurred. G0 headless execution remains a later separate gate.
The first G0 execution passed isolation and complete cleanup but not rendering:
only the AMD render node was visible, yet Hyprland exited before publishing the
headless output or using that node. Source preservation and zero residue passed.
A v2 ordinary internal-user correction is prepared but not executed.
V2 subsequently repeated complete isolation and cleanup but Aquamarine failed
to create its backend before opening AMD or publishing `HEADLESS-0`. A v3
bounded trace correction is prepared without broadening hardware access.
V3 repeated safe cleanup and retained the trace, but the trace still awaits an
authorized read after the host authentication window expired. Do not rerun G0
until that existing evidence is diagnosed.
The supplied trace identified the experiment's unsupported forced
`LIBSEAT_BACKEND=noop` as a concrete configuration defect. V4 removes that
override and preserves a crash report if needed; it is not yet executed.
V4 proved the remaining failure is absence of a seat session inside the
disposable container. V5 prepares a foreground, runtime-only seatd mediator
without a service or broader device visibility; it is not executed.
V5 then exposed a command-version mismatch before seatd started: Arch seatd
rejects the explicit `-s` option and already defaults to the intended socket.
V6 removes only that option and remains unexecuted.
V6 started seatd but the test runner failed while stopping its namespace
wrapper. Explicit recovery stopped the container and removed the v6 copy. V7
adds inner-process signaling and exception-safe emergency teardown.
V7 passed mediator lifecycle but seatd refused the client because no physical
VT exists. V8 uses the official non-VT-bound seat setting without adding KMS,
input, or any device.
V8 activated the non-VT seat but exposed an unusable nspawn bind entry. V9 uses
an ephemeral internal node for the identical AMD device number while the outer
device policy remains closed.
V9 still failed before the headless output and its protected diagnostic read
was authentication-blocked. V10 changes only new evidence ownership to the
Development identity; runtime and hardware boundaries are identical.
V10 proved the Aquamarine version ignores the arbitrary internal alias. V11
uses the standard render-node name for the same ephemeral `226:129` device.
V11 still failed to open it. V12 explicitly restores the real node's `0666`
mode after creation and captures the disposable user's pre-launch view.
V12 cleaned all observed runtime state but lost its final controller output
when the outer authorization wrapper stuck. V13 adds a bounded stage journal.
Its evidence remains executor-owned and only group-readable by Development, so
read access does not grant control over the privileged evidence path.
V13 then completed every outer isolation and teardown gate but repeated the
render failure. Aquamarine's source and retained trace establish that its DRM
backend selects canonical `cardN` paths; this physical render node is not an
independent compositor card. G0 must not widen to AMD `card2`, because that
would add physical KMS authority. The accepted next proof is G1 nested with no
direct DRM device; G2 alone may test exclusive KMS after KDE teardown.
G1 v1 then showed that private-user identity correctly blocks direct connection
to the owner-only KDE socket. V2 granted only the exact shifted UID through a
temporary, exactly restored ACL and reached the Wayland backend, but lacked an
allocator. V3 added only AMD `renderD129` and produced `WAYLAND-1`; v4 repeated
that proof while narrowing a controller teardown defect. V5 corrected direct
inner-Hyprland signaling and passed the complete nested gate: 1280×720/60
monitor evidence, internal screenshot, exit code 0, ACL restoration, unchanged
source, runtime removal, and zero process/mount residue. Direct Wayland protocol
exposure remains provisional and is not a final isolation result.
The G2 design now requires an independently recoverable broker surface,
authoritative KDE release, exact AMD KMS/render resolution, mediated selected
input, journaled grant and revocation, and verified return or safe recovery.
The candidate experiment boundary is now a host-owned text recovery VT plus a
separate Hyprland VT, temporary exact SDDM quiescence, and revocable per-run
device mediation. An executable physical-session preview remains blocked until
those mechanisms, the selected two-pass KDE/SDDM release evaluator, fixtures,
recovery rehearsal, and exact approval exist.
The first current-host read-only observation then found two live KDE session
generations on `seat0`: active Development on `tty4` and inactive Hub on `tty1`
through SDDM autologin. It also proved ordinary DRM descriptor scans are
insufficient as the sole KMS release authority. G2 must model and release both
sessions and add a version-bound DRM master/logind/lease observation before a
physical preview can be prepared.
The logical observer schema now defines automatic graphical-session discovery,
separate manager-session classification, closed evidence sources, independent
DRM fields, reboot invalidation, two immutable passes, and the three public
results. Pure evaluator and failure fixtures remain unimplemented.
The source-adapter proposal now maps every observer field to package, login1,
systemd, cgroup/proc, sysfs, kernel DRM, IPC, mount/namespace, KDE, or recovery
evidence and separates unprivileged, session-local, privileged-read, and effect
authority. Its first limits and failure fixtures are specified but unimplemented.

## Level 6: Attack and Recovery Campaign

Status: future.

Disposable Environments deliberately run malicious fixtures as normal user and
local root. Failures are injected during creation, activation, package
installation, stop, snapshot, archive, restore, and destroy.

The campaign tests:

- hostile package hooks and install scripts;
- resource exhaustion;
- namespace, capability, device, and socket escape attempts;
- stale approvals and journal tampering;
- forced power loss and executor restart;
- broken graphics and incomplete teardown;
- uncertain cleanup and protected-neighbour verification.

High-security shared-kernel tests cannot prove immunity to every future kernel
bug. Workloads requiring that promise need a separately tested virtual-machine
profile.

## User Test Experience

When Level 3 is ready, the user should receive one plain-language test preview:

- what will be created;
- how much storage and memory may be used;
- whether anything will be downloaded;
- which network and process activity will occur;
- confirmation that no personal Environment or Hub data is used;
- how the test stops;
- what cleanup would delete;
- which evidence will prove success or failure.

The user can approve the experiment without also approving cleanup, graphical
access, GPU access, or later levels. Each requires its own decision.

## Stop Conditions

Testing stops immediately when:

- host, Hub, base, or unrelated Environment state changes unexpectedly;
- an unavailable observation is needed to claim safety;
- identity or ownership becomes uncertain;
- quota or capacity enforcement is inconsistent;
- a process, mount, network object, device client, or session survives stop;
- a request accepts an unknown command, path, device, or policy;
- rollback would require guessing or deleting modified data;
- the observed isolation is weaker than the user-facing claim.

Stopping a test is a successful safety response, not permission to bypass the
failed check.

## Evidence and Handoff

Every level produces a concise report explaining:

- what was tested;
- what passed;
- what failed or could not be confirmed;
- what changed;
- what remained untouched;
- what data or resources remain;
- whether cleanup is safe and separately approved;
- whether the next level is eligible for review.

Technical logs remain bounded and separate. They do not contain unrelated
personal data or secrets.

## Current Readiness

Level 1 is established and growing. Level 2 has started with a repository-only
executor journal fixture. It tests ordered journal transitions, interrupted and
uncertain effects, corruption, stale writers, atomic replacement, restrictive
file modes, and symbolic-link refusal in disposable temporary directories. It
also tests canonical trust-evidence sealing, tamper detection, observer-class
boundaries, raw-diagnostic minimization, and strict parsing. It does not perform
lifecycle effects or use an authoritative host path. Pure capacity fixtures
also exercise dynamic growth, independent Environment/pool/physical ceilings,
host and metadata reserves, unhealthy quota states, and malformed evidence.
The pure installation fixture verifies that backup and recovery precede host
testing, KDE remains available through parallel graphical validation, cutover
does not imply cleanup, and complete evidence yields only cleanup review.
The Stage 2 final-gate fixture independently fails every boolean gate, rejects
cross-plan and malformed digests, and proves that complete evidence still
requires a separate execution approval.
The acquisition boundary fixture rejects alternate origins, insecure schemes,
redirects, URL credentials and suffixes, traversal, unsafe or duplicate names,
unreviewed repositories and architectures, ordering changes, byte-limit
violations, incomplete files, symbolic links, and transfer identity mismatch.
The disposable acquisition-staging fixture tests exclusive reservation,
plan-binding changes, restrictive modes, no-overwrite publication, bounded
streaming, exact hashes and sizes, preserved partial failures, symbolic-link
and non-regular-entry refusal, and unsafe parent or filename rejection.
The bounded downloader fixture simulates exact responses, redirects, status
failures, missing or contradictory lengths, early and excessive bodies,
digest disagreement, non-byte data, network/read/staging failures, and timeout
policy without making a network connection.
The direct HTTPS opener fixture verifies proxy suppression, redirect refusal,
TLS minimum and certificate/hostname requirements, fixed non-secret request
headers, strict archive authority, timeout bounds, response-URI identity, and
sanitized HTTP/network failures.
The transfer/staging integration fixture streams unknown database bytes in
small chunks, proves no final publication before matching evidence, preserves
partial bytes on simulated network failure, and refuses retry over an existing
partial operation.
One separately authorized real network fixture acquired only the dated Arch
`core.db` and `extra.db`, stayed within its per-file and aggregate bounds,
published exactly two regular files, and reproduced both hashes on independent
reopen. Package acquisition, extraction, and installation were not exercised.
Repository-database parser fixtures cover file digest and symlink refusal,
archive traversal and unexpected members, expansion bounds, duplicate package
and field identities, malformed text/numbers/hashes/signatures/architectures,
and canonical package metadata without extracting archive contents.
Closed-resolution fixtures reject missing seeds, duplicate or unknown packages,
malformed rows, version/architecture/filename/size/URL disagreement, missing
or duplicate database evidence, output/count/aggregate bounds, and bad plan
identity. The real offline resolver produced identical independent passes.
The fixed package acquisition reparses the authorized manifest before any
effect, produces exactly package/signature pairs, refuses existing or non-`/tmp`
roots, and blocks tampered evidence before network use. The real run stayed
bounded and its independent reopen verified 276 expected regular files.
Offline signature-verification fixtures reject cryptographic failure, missing
valid results, insufficient current master certification, and disagreement
between GnuPG and `gpgv`. The real run verified all 138 package/signature pairs
twice and both paths agreed on 15 trusted primary signing identities.
Package-metadata fixtures reject missing or duplicate identities, malformed or
oversized values, invalid sizes, and inside/outside identity disagreement. The
real bounded metadata-only run matched all 138 package archives without full
extraction, execution, installation, or network access.
Disposable-extraction fixtures reject absolute and parent-traversing archive
paths, invalid path encoding, oversized listings, non-`/tmp` targets, changed
receipts, excessive declared or observed storage, and special filesystem
entries. The real extraction stayed below 1 GiB; an independent tree walk
reproduced its file-type counts and byte totals with zero special entries.
Candidate-admission checks bind the extraction receipt to the live disposable
tree, require the minimal runtime, reject machine-local identity, report actual
ownership, and require a populated local pacman database. The real candidate
truthfully returned `not-admitted`; no boot or repair was attempted.
The authorized offline-root builder refuses non-administrator execution and an
existing destination, revalidates every fixed package hash, disables networking
around keyring and pacman operations, directs every mutable pacman path into the
new `/tmp` root, and enforces 138 local database entries and a 1 GiB ceiling.
Finalization accepts only the bound build report and removes only verified GPG
runtime sockets. The real build ended with 138 internal package records, zero
Development-owner entries, and zero special runtime entries.
The first-boot preview is deterministic and contains no execution capability.
Fixtures require the two-minute timeout, memory/CPU/task ceilings, private
network and user mapping, volatile source preservation, closed devices, no
machine registration, and no host bind, home path, port, or external network.
The first real attempt exercised fail-safe behavior: an option-format error
stopped before systemd, and post-checks found zero processes and mounts with the
source unchanged. The corrected comma-separated capability form has a new
preview digest and the executor refuses it until that digest is authorized.
The corrected attempt then proved a host compatibility limit: `/tmp` does not
support the requested ID-mapped mount. It also failed closed with no residue.
The next preview preserves private-user isolation through a new bounded runtime
copy and explicitly refuses to weaken the boundary or mutate the source root.
The authorized v3 run proved copy identity and complete cleanup but exposed an
nspawn incompatibility between ownership shifting and its read-only overlay.
V4 treats the already-disposable copy as the writable layer, preserving every
other isolation and cleanup gate while removing only the redundant overlay.
V4 ran to its timeout and proved cleanup/source preservation, but produced no
positive systemd readiness evidence and exposed an incompatible core rlimit.
V5 requires explicit console status and disables core storage through one fixed
policy inside the runtime copy instead of weakening private-user isolation.
V5 proved the same cleanup but confirmed that console output is not a usable
readiness channel here. V6 therefore requires bounded read-only `/proc`
observation of PID 1, four namespace identities, systemd runtime state, the
internal package count, and absence of the host Development home.
V6 proved early clean stop and complete cleanup but exposed an overly strict
observer assumption about systemd's mutable process title. V7 identifies
systemd by its executable and independently requires namespace PID 1 from the
kernel's read-only `NSpid` status.
V7 passed PID 1, four-namespace, systemd-runtime, 138-package, hidden-host-home,
clean-stop, cleanup, and source-preservation checks. Its target invocation
marker was structurally invalid for a target unit. V8 closes readiness through
the user-sessions service invocation and absence of the runtime login block.
V8 confirmed the user-session condition is genuinely not reached within the
observation window. V9 permits only fixed read-only systemctl queries for the
manager state, two named units, failed units, and pending jobs so the blocking
condition can be diagnosed without changing container state.
V9 reported system state `running`, both named units active, no failed units,
and no pending jobs. The final evidence-only assessment requires six independent
truths and passed all of them: boot, isolation, package boundary, session
readiness, clean lifecycle, and source preservation.
Complete-cleanup fixtures cover both user scopes, strong approval, exact
resource sets and digests, identity disagreement, runtime/open-handle/mount/
network and neighbor gates, `DELETED`, `<under deletion>`, `<stale>`, account
and registration residue, factual reclaim, pending identity reuse, and the
Hub's persistent read-only progress card.
Level 3
already has architecture and review documents, but its real
base, executor, authentication, quota topology, and host-changing approval are
not ready.

One separately authorized real-host quota leaf fixture and its complete cleanup
have passed. The path disappeared first while subvolume `263` and qgroup
`0/263` remained pending; only their later verified absence and healthy quota
state completed the test. This is evidence for one leaf, not permission to
treat hierarchical APX quota topology or Stage 3 Environment creation as ready.

The project must not describe future user testing as available until the exact
experiment preview, rollback boundary, and independently verified cleanup are
implemented and reviewed.

The Hub browser prototype is also a Level 1 fixture: Brave executes its
left-click, right-click, contextual-action, and management-view smoke tests
against in-memory data. This visual proof does not advance host readiness or
authorize Level 3.
