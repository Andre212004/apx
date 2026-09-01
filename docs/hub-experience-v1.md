# Hub Experience v1

Status: product flow and pure interface-state model implemented; no graphical
Hub application or working lifecycle buttons exist yet.

The graphical experience is now explicitly downstream of the headless `apx`
CLI. Every card and button must use the same typed request, preview, approval,
journal, result, and recovery contract as the corresponding CLI operation. The
CLI remains independently usable if the graphical Hub is absent or broken.

## Plain-Language Summary

The Hub is the APX home screen. It shows the owner's Environments as clear
cards and provides safe actions without exposing Linux accounts or technical
system tools.

The first useful Hub must allow the owner to:

- see which Environments exist and whether they are ready;
- create one from an approved model;
- open one;
- create a recovery point;
- archive or restore;
- delete with a clear data-loss warning;
- recover an interrupted operation;
- understand why an action is blocked.

The intended daily entry point is not the full management screen. A normal
Hyprland desktop has one APX control in its personalized taskbar. Left-clicking
that control expands approximately five Environment choices directly upward
from the icon. Left-clicking a choice requests the safe handoff. Right-clicking
a choice opens its contextual management actions. Right-clicking the main APX
control opens creation, archived Environments, and the complete management
screen described below.

The interface never decides that an operation is safe. It displays actions only
from confirmed APX state and sends one fixed request type to the protected
executor. Unknown state disables changes.

## Current Implementation

`src/apx_hub.py` implements a pure interface-state model. Given fake or future
verified Environment and template summaries, it produces cards, labels,
warnings, button availability, required confirmation strength, and fixed
request kinds.

It performs no file access, host observation, authentication, container launch,
or mutation. It is intentionally independent of the future graphical toolkit.

`prototypes/hub-demo` now implements the daily taskbar interaction and the
selected full-management visual direction as a dependency-free browser demo.
It uses only in-memory fixture data and cannot call the APX executor.

## Daily Taskbar Control

The APX taskbar icon has two distinct inputs:

- **Left click:** toggle a compact vertical Environment switcher attached to the
  icon. Each choice shows only icon, friendly name, and confirmed/warning state.
- **Right click:** open the APX management menu with Create new, View archived,
  and Open full management.

Each Environment choice also supports two inputs:

- **Left click:** request handoff when the state is confirmed safe; warning or
  unknown state opens verification instead.
- **Right click:** show only actions allowed for that Environment state, such as
  recovery point, archive, details, or delete with strong confirmation.

The switcher is not a conventional application menu and does not contain
packages, Linux accounts, host settings, recent documents, or arbitrary
commands. It is a fast chooser for the owner's small active set. Larger and
archived collections remain in full management.

## Home Screen

The default screen is titled “Os teus Environments”. It contains:

1. a small overall APX status;
2. Environment cards;
3. a “Create Environment” area using approved models;
4. restore and APX-status actions;
5. warnings requiring attention.

This future graphical screen does not embed a terminal, file browser, package
manager, web browser, Linux user list, service manager, or general host
settings. That restriction does not remove the separate, bounded `apx` CLI
from the initial headless Hub.

## Environment Card

Each card shows:

- friendly name;
- starting model;
- ready, active, incomplete, or unconfirmed state;
- understandable security profile;
- storage summary;
- actions currently safe to request.

Internal account names, storage UUIDs, plan digests, and backend names are
hidden by default. A bounded technical-details view may show them for support
without offering editing.

## Card States

### Ready to open

The card may offer:

- Open;
- Create recovery point;
- Archive;
- Delete;
- View details.

Delete uses strong confirmation. The other data-creating actions show their
storage and reversibility consequences before confirmation.

### Open now

The Hub normally cannot coexist graphically with a workload Environment. This
state is mainly useful to the transition/recovery model. Snapshot, archive, and
delete remain blocked until verified stop.

### Needs recovery

Normal actions disappear. The card offers recovery and read-only details. The
user is not encouraged to delete ambiguous state to remove the warning.

After deletion is approved, the card remains visible as `A limpar` with
read-only progress until complete cleanup evidence passes. The confirmation
offers only complete deletion, including every APX-owned copy, with strong
data-loss confirmation; snapshots and archives cannot be preserved by delete.
The name cannot be reused while the card remains. A stuck cleanup exposes
diagnostics and separately approved recovery, never an automatic force option.

### State unconfirmed

Only “Check again” and read-only details are available. The Hub explains that
no changes will be made until APX can confirm the state.

## Create Flow

Creation begins from an approved compatible template card, not a free-form
package or command screen.

The flow is:

1. choose a model such as University, Development, Games, or High Security;
2. choose a friendly Environment name;
3. review included main software;
4. review storage and resource expectations;
5. review internet, graphics, audio, camera, microphone, controller, and
   removable-device consequences;
6. review security-profile limitations;
7. show required downloads and approximate time where known;
8. confirm the exact creation plan;
9. show progress through plain-language stages;
10. verify completion before offering “Open”.

The user cannot enter a host path, Linux account, command, package-manager
argument, device node, or administrator option.

## Open and Return

Selecting Open first shows any known unsaved-Hub work or operation blockers.
After confirmation, the protected transition screen closes and verifies the
Hub before starting the selected Environment.

The Hub does not remain behind the new Environment. “Return to Hub” follows the
session handoff proposal and shows unsaved-work uncertainty honestly.

The button is not marked successful until the target graphical Environment is
verified ready.

## Recovery Point

The Hub explains that a recovery point:

- requires the Environment to be stopped;
- consumes storage, although unchanged data may share physical space;
- protects against later software/configuration damage;
- is not by itself an external backup;
- does not guarantee reversal of remote accounts or external service changes.

The resulting copy appears in the Environment details screen with creation
date, source state, size information where trustworthy, and retention choice.

## Archive and Restore

Archive creates a longer-lived verified copy from an existing recovery point.
The Hub shows whether the archive remains only on the same physical storage and
therefore is not protection against disk failure.

Restore always creates a new Environment identity in v1. The screen requests a
new friendly name and clearly states that runtime sessions, device approvals,
credentials, and Hub powers are not restored automatically.

## Delete Flow

Delete is never a single accidental click. The confirmation screen shows:

- exact Environment friendly name;
- applications and local system state that will disappear;
- measured home/root data where trustworthy;
- recovery points and archives that will remain;
- whether recovery is possible afterwards;
- any unknown measurement;
- requirement for fresh strong confirmation.

The final control uses an explicit phrase such as “Delete this Environment”. It
does not use misleading labels such as “Clean”, “Reset”, or “Free space”.

An active, incomplete, unconfirmed, or identity-conflicting Environment cannot
be deleted through the normal flow.

## Operation Progress

Long actions show semantic stages rather than raw commands:

- Checking safety;
- Preparing isolated storage;
- Creating the Environment;
- Verifying separation;
- Finishing registration;
- Ready;
- Stopped safely;
- Needs attention.

Cancel appears only before or between phases where cancellation is proven safe.
Closing the visual window does not cancel or hide a protected operation.

## Failure and Recovery Screen

When an action fails, the Hub explains:

- what APX was trying to do;
- whether any files were changed;
- whether the original Environment remains usable;
- whether incomplete resources remain;
- which safe choices are available;
- whether new confirmation is required.

The normal choices are retry checks, complete recovery, preserve for inspection,
return to Hub, lock, or separately approve cleanup. No “ignore and continue”
button converts unknown safety into success.

## Overall APX States

The interface recognizes:

- **Ready:** normal management actions are available;
- **Busy:** one operation is running; new changes are blocked;
- **Incomplete:** recovery is required;
- **Unavailable:** APX cannot confirm current state and makes no changes.

Detecting more than one active graphical Environment is always incomplete and
blocks new mutations.

## Approved Templates

Only templates that are admitted and compatible can show an enabled Create
button. An unapproved model remains visible only when useful for explaining why
it cannot be used.

The template card shows purpose, main software, security profile, approximate
storage, compatibility, and important device/network consequences. It never
carries a package list or command to the executor.

## Accessibility and Language

The first graphical implementation must support keyboard navigation, visible
focus, screen-reader labels, scalable text, adequate contrast, reduced motion,
and operation status that does not rely only on colour.

User-facing text defaults to ordinary language. Technical terms have short
explanations. Destructive confirmation never depends on an icon alone.

Portuguese and English strings must be separate resources rather than mixed
inside lifecycle code. The current pure model uses Portuguese fixture text to
validate clarity; localization extraction remains implementation work.

## Privacy

Cards do not show document names, recent files, browser history, source
repositories, assistant conversations, or window titles. Storage and activity
summaries reveal only what is necessary to manage the selected Environment.

The Hub does not inspect workload content to create recommendations.

## Graphical Technology

The final toolkit remains open. The pure view model avoids tying security and
lifecycle rules to GTK, Qt, a web view, a compositor, or a specific desktop.

Toolkit selection and a real graphical Hub begin only after the clean-bootstrap
C0–C6 gates and H0 pass. The browser demo does not change that order.

Selection criteria include:

- runs on Hyprland, KDE Plasma, and GNOME;
- strong keyboard and accessibility support;
- small, reviewable dependency and update surface;
- no requirement for a general-purpose browser in the Hub;
- clear separation between presentation and executor requests;
- reliable full-screen recovery/transition behavior;
- package availability inside the Hub template.

The first graphical prototype may use fake fixture data. It must be visibly
labelled “Demo data” and cannot connect buttons to host mutation.

## Acceptance Gates

Before the user tests the working Hub:

1. Connect cards only to authoritative registration and lifecycle observations.
2. Implement strict creation-name and template selection without free-form host
   inputs.
3. Connect action requests to the executor contract, not direct commands.
4. Implement approval previews and strong destructive confirmation.
5. Implement operation progress, restart recovery, and unconfirmed-state blocks.
6. Select and accessibility-test the graphical toolkit.
7. Test the complete interface first with demo data and a fake executor.
8. Test one disposable headless Environment before enabling graphical launch.
9. Prove no button can bypass the same backend gates enforced outside the UI.
10. Complete Hub-to-Environment and return testing on a disposable profile.

No acceptance gate authorizes installing or launching the graphical Hub on the
real host.
