#!/usr/bin/env python3
"""Fixed Host network boundary for the first owner-built headless Hub."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


TABLE = "apx_hub_egress_v1"
INTERFACE = "ve-apx-hub"
PRIVATE_IPV4 = "{ 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16 }"


class NetworkPolicyError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], *, check: bool = True,
        input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, input=input_text, text=True, capture_output=True, check=check,
        env={"PATH": "/usr/bin", "LC_ALL": "C"},
    )


def ruleset() -> str:
    return f"""table inet {TABLE} {{
 chain host_input {{
  type filter hook input priority -5; policy accept;
  iifname "{INTERFACE}" udp dport 67 accept
  iifname "{INTERFACE}" drop
 }}
 chain environment_forward {{
  type filter hook forward priority -5; policy accept;
  iifname "{INTERFACE}" ip daddr {PRIVATE_IPV4} drop
  iifname "{INTERFACE}" oifname "ve-*" drop
 }}
}}
"""


def table_exists() -> bool:
    return run(("/usr/bin/nft", "list", "table", "inet", TABLE), check=False).returncode == 0


def apply() -> None:
    if table_exists():
        observed = run(("/usr/bin/nft", "list", "table", "inet", TABLE)).stdout
        for required in (INTERFACE, "udp dport 67 accept", "ip daddr",
                         "oifname \"ve-*\" drop"):
            if required not in observed:
                raise NetworkPolicyError("existing APX Hub network policy differs")
        return
    run(("/usr/bin/nft", "-c", "-f", "-"), input_text=ruleset())
    run(("/usr/bin/nft", "-f", "-"), input_text=ruleset())
    if not table_exists():
        raise NetworkPolicyError("APX Hub network policy did not appear")


def remove() -> None:
    if table_exists():
        run(("/usr/bin/nft", "delete", "table", "inet", TABLE))
    if table_exists():
        raise NetworkPolicyError("APX Hub network policy survived removal")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("apply", "remove"))
    parser.add_argument("--environment", required=True)
    arguments = parser.parse_args()
    if os.geteuid() != 0 or arguments.environment != "hub":
        raise NetworkPolicyError("network policy identity or privilege differs")
    apply() if arguments.mode == "apply" else remove()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NetworkPolicyError, subprocess.CalledProcessError) as error:
        print(f"APX network policy refused: {error}", file=sys.stderr)
        raise SystemExit(2)
