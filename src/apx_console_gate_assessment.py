"""Final evidence-only assessment of the first APX console lifecycle gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path

from apx_offline_base_build import ROOT


REPORT = ROOT / "first-boot-report-v9.json"
AUTHORIZED_REPORT = "f129d383b0b6c4cc8a80882a46a7237c16becb76693a1af97b2f20ea11b44432"


class ConsoleGateAssessmentError(RuntimeError):
    """The final console evidence is missing, changed, or incomplete."""


@dataclass(frozen=True)
class ConsoleGateAssessment:
    schema_version: int
    status: str
    boot_proven: bool
    isolation_proven: bool
    package_boundary_proven: bool
    session_readiness_proven: bool
    clean_lifecycle_proven: bool
    source_preservation_proven: bool
    source_report_digest: str
    assessment_digest: str


def assess_payload(payload: dict) -> ConsoleGateAssessment:
    digest = payload.get("report_digest")
    unsigned = dict(payload); unsigned.pop("report_digest", None)
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    if digest != AUTHORIZED_REPORT or hashlib.sha256(canonical.encode()).hexdigest() != digest:
        raise ConsoleGateAssessmentError("v9 boot report identity changed")
    boot = payload.get("systemd_started") is True and payload.get("pid1_systemd_observed") is True
    isolation = payload.get("private_namespaces_observed") is True and payload.get("host_development_home_hidden") is True
    packages = payload.get("internal_package_count") == 138
    sessions = (
        payload.get("system_state_query") == "running"
        and payload.get("named_units_query") == ["active", "active"]
        and payload.get("failed_units_query") == []
        and payload.get("pending_jobs_query") == []
    )
    lifecycle = (
        payload.get("clean_shutdown_observed") is True
        and payload.get("process_exit_code") == 0
        and payload.get("matching_processes_after") == 0
        and payload.get("matching_mounts_after") == 0
        and payload.get("runtime_copy_removed") is True
    )
    source = payload.get("source_report_unchanged") is True
    draft = {
        "schema_version": 1,
        "status": "passed" if all((boot, isolation, packages, sessions, lifecycle, source)) else "failed",
        "boot_proven": boot, "isolation_proven": isolation,
        "package_boundary_proven": packages, "session_readiness_proven": sessions,
        "clean_lifecycle_proven": lifecycle, "source_preservation_proven": source,
        "source_report_digest": digest,
    }
    assessment_digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return ConsoleGateAssessment(**draft, assessment_digest=assessment_digest)


def assess_console_gate() -> ConsoleGateAssessment:
    try:
        payload = json.loads(REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConsoleGateAssessmentError("v9 boot report is unavailable") from error
    assessment = assess_payload(payload)
    descriptor = os.open(ROOT / "console-gate-assessment.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(asdict(assessment), sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return assessment


def main() -> int:
    result = assess_console_gate()
    print("APX first console lifecycle gate")
    print(f"Status: {result.status}")
    print(f"Boot: {result.boot_proven}")
    print(f"Isolation: {result.isolation_proven}")
    print(f"Own package boundary: {result.package_boundary_proven}")
    print(f"Session readiness: {result.session_readiness_proven}")
    print(f"Clean lifecycle: {result.clean_lifecycle_proven}")
    print(f"Source preserved: {result.source_preservation_proven}")
    print(f"Assessment digest: {result.assessment_digest}")
    return 0 if result.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
