# Session Management

This document records the confirmed intended APX session model and the parts that still require validation.

## Current System

No functional APX session-management implementation currently exists.

SDDM currently manages graphical sessions. `greetd` has not been adopted or implemented.

Current manually created users have ordinary homes under the existing `@home` subvolume rather than dedicated Btrfs home subvolumes.

## Confirmed Intended Architecture

Each Environment is represented by a dedicated Linux user.

Each Environment is intended to have its own Btrfs home subvolume. This is not yet true for the current manually created users, which still have ordinary homes under the existing `@home` subvolume.

KDE Plasma is shared at the system level. Environment separation comes from Linux users, home data, user configuration, session state, user-owned processes, and APX metadata.

The Hub is the default Environment.

Only one graphical Environment should run at a time in the intended APX model.

The intended flow is:

```text
Boot -> Hub -> Environment -> Hub
```

The Hub must be destroyable and recreatable like every other Environment.

No implementation decision may require a unique lifecycle exception for the Hub.

## Intended Flow

### Boot to Hub

The target system boots into the Hub as the default APX Environment.

The Hub is intended to provide APX management workflows:

- list Environments
- create Environments
- archive Environments
- restore Environments
- snapshot Environments
- manage templates
- launch Environments

The Hub is not a general-purpose desktop. It is the APX management entry point.

### Hub to Environment

In the intended flow, the user launches an Environment from the Hub.

The target model should ensure that only the selected graphical Environment is active. The previous graphical Environment should not remain as an independent concurrent desktop session.

### Environment to Hub

In the intended flow, control returns to the Hub when the user exits or switches away from an Environment.

APX lifecycle operations must account for running user-owned processes before archive, restore, snapshot, destruction, or session handoff operations occur.

## KDE Plasma

KDE Plasma is installed once at the system level.

Each Environment is intended to have separate KDE configuration and session state through its dedicated Linux user and home data.

APX should not install or manage a separate KDE Plasma copy per Environment.

## Display Manager Direction

`greetd` is only the preferred direction under evaluation for future APX session handoff. It has not been adopted or implemented.

SDDM currently manages graphical sessions.

The display-manager decision must be validated before implementation changes are made.

## Process Model

Processes belong to the Linux user that launched them.

APX should treat process ownership as part of the Environment boundary.

Process isolation through Linux namespaces is not implemented and is not a confirmed requirement.

## Storage Model

The intended storage model is one Btrfs home subvolume per Environment.

This is intended to support:

- snapshots
- archival
- restoration
- templates
- clean lifecycle operations

The current manually created users still have ordinary homes under the existing `@home` subvolume.

## Ideas Under Evaluation

- Replace SDDM with `greetd` for APX-controlled session handoff.
- Use APX metadata to track each Environment's user, home subvolume, state, snapshots, archives, and template origin.

## Open Questions

- What is the exact technical handoff mechanism from Hub to another Environment and back?
- How should APX handle unsaved work or long-running processes during Environment switching?
- Should APX terminate, suspend, or refuse switching when user-owned processes are still running?
- How should authentication work for launching another Environment from the Hub?
- What minimal permissions does the Hub need to manage other Environments?
- What display-manager/session-manager integration provides the cleanest model without making the Hub special?
