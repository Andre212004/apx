# Hub

The Hub is the APX management Environment.

It is not a desktop replacement, development workspace, or general-purpose user environment.

## Responsibilities

The Hub is responsible for:

- listing Environments
- creating Environments
- archiving Environments
- restoring Environments
- creating snapshots
- managing templates
- launching Environments

## Strict Boundaries

The Hub must not contain APX development work.

The following do not belong in the Hub:

- source repositories
- IDEs
- build tools
- development browsers or profiles
- Git workflow tools
- implementation artifacts
- experimental development scripts

These belong in the APX Development Environment.

## No Special Architectural Exceptions

The Hub is still an Environment.

It may have APX management permissions, but it should not bypass the core APX model without a documented architectural decision.

## Design Direction

The Hub should be simple, focused, and operational.

It should expose APX management workflows without becoming a full desktop or hiding the underlying Environment model.

