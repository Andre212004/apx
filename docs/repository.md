# Repository

This repository starts as a documentation-first APX foundation.

## Foundation Phase

During the foundation phase, the repository should contain:

- project README
- architecture documentation
- Environment model documentation
- Hub documentation
- Development Environment documentation
- repository conventions

It should not contain implementation code until the architecture is documented well enough to guide it.

## Future Structure

Future implementation directories should be added only when their role is clear.

Likely future areas may include:

- command-line tooling
- Hub application code
- lifecycle management services
- tests
- packaging

These directories are intentionally not created yet because the current goal is project foundation, not implementation.

## Documentation Standards

Documentation should be:

- explicit about architectural boundaries
- concise but complete enough to guide implementation
- updated before or alongside architectural changes
- free of unnecessary abstractions
- consistent with APX design principles

## Git History

The initial commit should establish the documentation-first foundation.

Subsequent commits should keep related documentation and implementation changes together when the implementation depends on a documented decision.

