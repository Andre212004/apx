# APX Hyprland H0 Clean-Host Gate v1

Status: pure readiness, preview, ordered journal, and conservative recovery
implemented. No physical graphical package installation, VT switch, device
grant, input mediator, compositor launch, watchdog, teardown adapter, or Host
change is implemented or authorized.

## Practical Goal

H0 is the first time the clean headless APX pilot will show a real graphical
Environment on the laptop display. It is deliberately smaller than the final
desktop experience:

- one disposable Hyprland Environment;
- the AMD integrated GPU only;
- the built-in keyboard and touchpad only, through a mediator;
- no NVIDIA GPU;
- no audio, camera, microphone, broad input, Host filesystem, or executor;
- one independent text recovery console kept available;
- a five-minute maximum experiment;
- mandatory return to the verified headless Hub path.

Passing H0 proves the physical display/session boundary. It does not yet make
Hyprland the normal login, install a graphical Hub, or approve daily graphical
use.

## Why H0 Is Separate From G2

The older G2 work was designed for switching away from an existing KDE/SDDM
desktop. The physical pilot now starts headless and has no display manager, so
it does not need KDE logout or SDDM shutdown. H0 instead proves that no graphical
owner exists before granting the display.

G0 and G1 remain useful evidence: the graphical role was resolved, packages
were verified, a disposable graphical root was built, and nested Hyprland
rendered successfully. H0 reuses that evidence but introduces the physical KMS,
input, VT, watchdog, and return-to-headless boundary.

## Readiness Evidence

`H0Evidence` in `src/apx_hyprland_h0.py` requires:

- reconciled physical audit and exact machine/marker identity;
- no display manager installed, enabled, or active;
- no graphical session owner or stale graphical lease;
- independently identified and tested recovery VT;
- healthy headless Hub and Development;
- no uncertain APX operation;
- target AMD PCI `0000:05:00.0` using `amdgpu`;
- exact AMD GPU, KMS, render, and connector identities;
- known NVIDIA PCI `0000:01:00.0` explicitly excluded;
- exactly two distinct mediated input identities: built-in keyboard and
  built-in touchpad;
- explicit absence of broad input, audio, camera, microphone, Host filesystem,
  and executor access;
- graphical release, package evidence, Hyprland configuration, APX return
  control, disposable generation, watchdog, timeout, and teardown observer
  identities.

An arbitrary device path cannot be supplied in the schema. The future trusted
observer resolves device paths from the recorded identities.

## Preview and Approval

Complete evidence produces only `ready-for-separate-physical-approval`. The
preview lists the exact AMD and input scope, timeout, Environment generation,
effects, and consequences. It does not contain a command or grant authority.

The separate physical approval must explain:

- Hub and Development will stop for the experiment;
- the laptop display and selected input temporarily belong to one disposable
  Environment;
- NVIDIA, audio, camera, microphone, and other input remain unavailable;
- a failure returns control to the text recovery path;
- cleanup is not included and needs separate evidence and approval.

Tomorrow's general audit is necessary but not sufficient. A later H0-specific
read-only capture must identify the actual AMD connector/card/render nodes,
built-in keyboard/touchpad, VTs, and current package/runtime state.

## Ordered H0 Experiment

`src/apx_hyprland_h0_journal.py` fixes this sequence:

1. reverify clean Host and independent recovery VT;
2. stop headless Hub and Development cleanly;
3. reserve one generation-bound graphical lease;
4. grant only exact AMD KMS and render devices;
5. grant only mediated built-in keyboard and touchpad;
6. start disposable Hyprland on the experiment VT;
7. verify Wayland output, input, and APX return control;
8. enforce watchdog and continued recovery-VT availability;
9. stop Hyprland and revoke every device;
10. prove zero residue and restore the headless Hub path.

Every step is prepared before it may be recorded complete. Evidence digests and
the chained journal prevent skipped steps, changed identities, replay, and two
writers silently advancing different versions of the experiment.

## Failure Behaviour

A black screen, compositor crash, timeout, missing input, VT failure, unplugged
display, device identity change, or uncertain effect never triggers an automatic
graphical restart. The recovery model requires the independent text VT and
blocks another graphical session.

The journal distinguishes:

- no effect recorded;
- partial device/session preparation;
- graphical session possibly active;
- partial teardown;
- unknown prepared effect;
- explicit preserve-and-inspect state;
- complete verified return to headless operation.

Only the final state may claim that the Hub path is restored. Path disappearance
or a dead Hyprland process is not enough; GPU, input, VT, processes, mounts,
leases, and APX state all need fresh absence evidence.

## Path From H0 to a GUI

After H0 passes physically, development proceeds in this order:

1. repeat H0 with failure injection and reliable return to Hub;
2. create a durable Hyprland role release rather than a disposable fixture;
3. add the APX return/switch control inside that Environment;
4. connect that control to the same typed APX previews used by the CLI;
5. test keyboard navigation, visible focus, readable warnings, and failure
   recovery;
6. build a graphical Hub client using `src/apx_hub.py` state;
7. keep the CLI and text recovery path independently usable;
8. only then decide whether the graphical Hub becomes the default.

The existing `prototypes/hub-demo` is a visual prototype, not the installed
GUI. It can guide appearance and interaction after H0 proves the physical
session boundary.

## Remaining Implementation Gates

Before physical H0, the repository still needs:

1. reviewed results from the physical audit;
2. H0-specific read-only device, input, connector, and VT observations;
3. selected physical graphical backend and minimum privileges;
4. a host-owned VT/recovery controller;
5. an exact AMD device lease and built-in input mediator;
6. a reproducible graphical role compatible with the installed pilot runtime;
7. watchdog, teardown, and zero-residue physical observers;
8. failure fixtures for every ordered effect;
9. a target-bound H0 dossier and explicit owner approval.

Do not install Hyprland on the Host or expose `/dev/dri`, `/dev/input`, or a
host Wayland socket broadly to make the experiment work.
