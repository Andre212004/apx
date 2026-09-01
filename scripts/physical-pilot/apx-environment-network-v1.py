#!/usr/bin/env python3
"""Fixed Host network boundary for the first owner-built headless Hub."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys


NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,7}")
PRIVATE_IPV4 = "{ 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16 }"


class NetworkPolicyError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], *, check: bool = True,
        input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, input=input_text, text=True, capture_output=True, check=check,
        env={"PATH": "/usr/bin", "LC_ALL": "C"},
    )


def identities(environment: str) -> tuple[str, str]:
    if NAME.fullmatch(environment) is None:
        raise NetworkPolicyError("graphical network identity is too long or malformed")
    return "apx_" + environment.replace("-", "_") + "_egress_v1", "ve-apx-" + environment


def ruleset(table: str, interface: str) -> str:
    return f"""table inet {table} {{
 chain host_input {{
  type filter hook input priority -5; policy accept;
  iifname "{interface}" udp dport 67 accept
  iifname "{interface}" drop
 }}
 chain environment_forward {{
  type filter hook forward priority -5; policy accept;
  iifname "{interface}" ip daddr {PRIVATE_IPV4} drop
  iifname "{interface}" oifname "ve-*" drop
 }}
}}
"""


def table_exists(table: str) -> bool:
    return run(("/usr/bin/nft", "list", "table", "inet", table), check=False).returncode == 0


def apply(environment: str) -> None:
    table, interface = identities(environment)
    if table_exists(table):
        observed = run(("/usr/bin/nft", "list", "table", "inet", table)).stdout
        for required in (interface, "udp dport 67 accept", "ip daddr",
                         "oifname \"ve-*\" drop"):
            if required not in observed:
                raise NetworkPolicyError("existing APX Hub network policy differs")
        return
    rendered = ruleset(table, interface)
    run(("/usr/bin/nft", "-c", "-f", "-"), input_text=rendered)
    run(("/usr/bin/nft", "-f", "-"), input_text=rendered)
    if not table_exists(table):
        raise NetworkPolicyError("APX Hub network policy did not appear")


def remove(environment: str) -> None:
    table, _interface = identities(environment)
    if table_exists(table):
        run(("/usr/bin/nft", "delete", "table", "inet", table))
    if table_exists(table):
        raise NetworkPolicyError("APX Hub network policy survived removal")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("apply", "remove"))
    parser.add_argument("--environment", required=True)
    arguments = parser.parse_args()
    if os.geteuid() != 0:
        raise NetworkPolicyError("network policy identity or privilege differs")
    apply(arguments.environment) if arguments.mode == "apply" else remove(arguments.environment)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NetworkPolicyError, subprocess.CalledProcessError) as error:
        print(f"APX network policy refused: {error}", file=sys.stderr)
        raise SystemExit(2)
