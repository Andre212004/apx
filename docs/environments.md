# Environments

An Environment is an isolated personal workspace managed by APX.

Each Environment combines Linux identity, storage, session state, processes, and metadata into a coherent unit.

## Required Components

Every Environment has:

- one Linux user
- one Btrfs subvolume
- one independent KDE session
- independent user configuration
- independent user-owned processes
- independent APX metadata

## Linux User

The Linux user is the primary identity boundary.

It defines:

- file ownership
- process ownership
- user-level permissions
- home directory ownership
- session identity

APX should avoid creating hidden alternate identity systems when Linux users already provide the required primitive.

## Btrfs Subvolume

Each Environment has its own Btrfs subvolume.

The subvolume provides a clear storage boundary and supports lifecycle operations such as snapshots, archival, restoration, and templates.

The exact subvolume layout should be documented before implementation.

## KDE Session

Each Environment has its own independent KDE session.

Session independence means Environment-specific desktop configuration, application state, and user-level services do not leak into another Environment.

## Processes

Processes belong to the Environment user that launched them.

APX should treat process ownership as part of the Environment boundary. Lifecycle operations that stop, archive, restore, or switch Environments must account for running processes.

## Metadata

Each Environment needs APX-managed metadata.

Metadata may include:

- Environment identifier
- display name
- lifecycle state
- associated Linux user
- associated Btrfs subvolume
- creation time
- archival state
- template origin
- snapshot references

The metadata format should be simple, explicit, and documented before implementation.

## Lifecycle States

Initial lifecycle concepts:

- active
- archived
- restorable
- template

These states are provisional and should be refined when lifecycle workflows are specified in detail.

