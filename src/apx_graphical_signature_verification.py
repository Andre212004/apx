"""Double offline signature verification for the closed Hyprland role set."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path

from apx_graphical_acquisition import AUTHORIZED_MANIFEST, MANIFEST_PATH, ROOT as ACQUISITION_ROOT
from apx_graphical_resolution import parse_graphical_manifest
from apx_signature_verification import (
    KEYRING, REVOKED, TRUSTED, TRUST_INPUT_HASHES, SignatureEvidence,
    SignatureVerificationError, _regular, _run, _sha256, _write_exclusive,
    parse_fingerprints, parse_master_certifications, parse_valid_signature,
    trust_is_sufficient,
)


ROOT = Path("/tmp/apx-hyprland-signature-verification-20260711-v2")
PACKAGE_ROOT = ACQUISITION_ROOT / ("op-" + AUTHORIZED_MANIFEST[:32]) / "files"


@dataclass(frozen=True)
class GraphicalSignatureReport:
    schema_version: int
    manifest_digest: str
    package_count: int
    unique_signers: tuple[str, ...]
    evidence: tuple[SignatureEvidence, ...]
    evidence_digest: str


def verify_graphical_signatures() -> GraphicalSignatureReport:
    manifest = parse_graphical_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.manifest_digest != AUTHORIZED_MANIFEST or len(manifest.role_packages) != 194:
        raise SignatureVerificationError("graphical manifest is not the authorized closed set")
    for path, expected in TRUST_INPUT_HASHES.items():
        _regular(path)
        if _sha256(path) != expected:
            raise SignatureVerificationError("installed Arch trust material changed")
    trusted, revoked = parse_fingerprints(TRUSTED), parse_fingerprints(REVOKED)
    try:
        os.mkdir(ROOT, 0o700)
    except FileExistsError as error:
        raise SignatureVerificationError("graphical verification root exists; refusing adoption") from error
    home = ROOT / "gnupg"; home.mkdir(mode=0o700)
    base = ("/usr/bin/gpg", "--batch", "--no-autostart", "--homedir", str(home))
    _run(base + ("--import", str(KEYRING)))
    first_pass = []; cache: dict[str, tuple[str, ...]] = {}
    for item in manifest.role_packages:
        package, signature = PACKAGE_ROOT / item.filename, PACKAGE_ROOT / (item.filename + ".sig")
        _regular(package); _regular(signature)
        package_hash = _sha256(package)
        if package_hash != item.sha256:
            raise SignatureVerificationError("graphical package bytes changed")
        signer, primary = parse_valid_signature(
            _run(base + ("--status-fd", "1", "--verify", str(signature), str(package)))
        )
        if signer in revoked or primary in revoked:
            raise SignatureVerificationError("graphical package signer is revoked")
        if primary not in cache:
            cache[primary] = parse_master_certifications(
                _run(base + ("--with-colons", "--check-sigs", primary)), trusted
            )
        if not trust_is_sufficient(primary, cache[primary], trusted):
            raise SignatureVerificationError("graphical signer lacks current Arch master trust")
        first_pass.append(SignatureEvidence(
            item.filename, package_hash, _sha256(signature), signer, primary,
            cache[primary], True, False,
        ))
    exported = _run(base + ("--export",), binary=True)
    if not isinstance(exported, bytes):
        raise SignatureVerificationError("independent key export type is invalid")
    independent_keyring = ROOT / "independent-keyring.gpg"
    _write_exclusive(independent_keyring, exported)
    completed = []
    for item, evidence in zip(manifest.role_packages, first_pass):
        package, signature = PACKAGE_ROOT / item.filename, PACKAGE_ROOT / (item.filename + ".sig")
        signer, primary = parse_valid_signature(_run(
            ("/usr/bin/gpgv", "--status-fd", "1", "--keyring", str(independent_keyring),
             str(signature), str(package))
        ))
        if (signer, primary) != (evidence.signer_fingerprint, evidence.primary_fingerprint):
            raise SignatureVerificationError("independent verifier identified a different graphical signer")
        completed.append(SignatureEvidence(**{**asdict(evidence), "independent_valid": True}))
    unsigned = {
        "schema_version": 1, "manifest_digest": manifest.manifest_digest,
        "package_count": len(completed),
        "unique_signers": sorted({item.primary_fingerprint for item in completed}),
        "evidence": [asdict(item) for item in completed],
    }
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    payload = {**unsigned, "evidence_digest": digest}
    _write_exclusive(ROOT / "graphical-signature-evidence.json",
                     (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode())
    return GraphicalSignatureReport(
        1, manifest.manifest_digest, len(completed), tuple(unsigned["unique_signers"]),
        tuple(completed), digest,
    )


def main() -> int:
    report = verify_graphical_signatures()
    print("APX Hyprland offline signature verification")
    print(f"Packages verified twice: {report.package_count}")
    print(f"Trusted signing identities: {len(report.unique_signers)}")
    print(f"Evidence digest: {report.evidence_digest}")
    print("Network/install/extract/execute/GPU/system/cleanup effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
