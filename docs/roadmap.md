# Roadmap

This roadmap is intentionally documentation-first. It records likely project phases without treating unresolved design work as implementation-ready.

## Phase 0: Repository Foundation

Status: in progress.

Goals:

- maintain a clean repository structure
- document APX architecture
- document session-management direction
- document development principles
- identify unresolved design questions
- avoid implementation code until architecture is ready

## Phase 1: Architecture Validation

Status: not started.

Goals:

- validate the Btrfs subvolume layout
- validate the Environment metadata model
- validate the session handoff model
- validate Hub permissions
- validate lifecycle states and transitions
- decide whether `greetd` should replace SDDM

## Phase 2: Minimal Prototype Design

Status: not started.

Goals:

- define the smallest APX command or management surface needed for validation
- specify non-destructive test scenarios
- document rollback and recovery expectations
- define how the prototype avoids modifying real system state without explicit approval

No prototype implementation should begin until Phase 1 decisions are documented.

## Phase 3: Environment Lifecycle Implementation

Status: not started.

Possible scope:

- list Environments
- create Environments
- archive Environments
- restore Environments
- snapshot Environments
- manage templates
- launch Environments

This phase depends on validated storage, metadata, permissions, and session-management decisions.

## Phase 4: Hub Experience

Status: not started.

Possible scope:

- APX management interface
- Environment launcher
- snapshot, archive, restore, and template workflows
- status and validation reporting

The Hub must remain an Environment and must not require unique lifecycle exceptions.

## Current System

- No functional APX implementation currently exists.
- Development currently takes place in `apx-development`.
- SDDM currently manages graphical sessions.
- Current manually created users have ordinary homes under the existing `@home` subvolume.
- Codex is a temporary development tool and is not part of APX.

## Confirmed Intended Architecture

- APX is an orchestration layer on one Arch Linux installation.
- The host has one kernel, one package database, and one system-level KDE Plasma installation.
- Applications are globally installed.
- Each Environment corresponds to one dedicated Linux user and one intended dedicated Btrfs home subvolume.
- Environment data and configuration are isolated per Environment.
- The Hub is the default APX Environment and management entry point.
- The Hub must be destroyable and recreatable like every other Environment.
- The intended lifecycle is `Boot -> Hub -> Environment -> Hub`.
- Only one graphical Environment is active at a time in the intended model.
- Linux user ownership is sufficient as the primary identity boundary.
- APX should avoid namespaces unless a future design proves they are necessary.

## Ideas Under Evaluation

- `greetd` is the preferred candidate under evaluation for APX session handoff.
- APX metadata may track Environment identifiers, display names, lifecycle states, Linux users, Btrfs subvolumes, creation times, archival states, template origins, and snapshot references.

## Open Questions

- What exact Btrfs subvolume layout should APX use?
- What exact Environment metadata format should APX use?
- What is the safest session handoff mechanism?
- What permissions should the Hub have?
- How should APX handle running processes during switching, archive, restore, and destruction?
- What recovery model is required if Environment launch or return-to-Hub fails?
- What tests are required before APX can modify real users, homes, sessions, or subvolumes?
