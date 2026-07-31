"""Fixed entry point for the local APX typed executor service."""

from __future__ import annotations

from apx_executor_authorities import build_authorities
from apx_executor_server import serve
from apx_graphical_effect_adapter import apply_graphical_effect


def authority_factory(credentials):
    return build_authorities(credentials, apply_graphical_effect)


def main() -> int:
    serve(authority_factory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
