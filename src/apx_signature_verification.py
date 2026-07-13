"""Offline, fail-closed verification of the fixed Arch package acquisition."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

from apx_package_acquisition import AUTHORIZED_MANIFEST, MANIFEST_PATH, ROOT as ACQUISITION_ROOT
from apx_resolution import parse_resolution_manifest


ROOT = Path("/tmp/apx-signature-verification-20260711-v1")
PACKAGE_ROOT = ACQUISITION_ROOT / ("op-" + AUTHORIZED_MANIFEST[:32]) / "files"
KEYRING = Path("/usr/share/pacman/keyrings/archlinux.gpg")
TRUSTED = Path("/usr/share/pacman/keyrings/archlinux-trusted")
REVOKED = Path("/usr/share/pacman/keyrings/archlinux-revoked")
TRUST_INPUT_HASHES = {
    KEYRING: "4f9f55c7702ff580f808a86e4eeed7d471252684c03089427c69796e88253516",
    TRUSTED: "384c7daf07a89ec6610859142b009ca5c0b3062ed3ab2d3c50629fef9d002e8f",
    REVOKED: "aafbc33d6be7e200dd6226dbb467623a38a00db431826258bccfaf5cebfef6a1",
}
BAD_STATUS = {"BADSIG", "ERRSIG", "NO_PUBKEY", "REVKEYSIG", "EXPKEYSIG", "KEYEXPIRED", "SIGEXPIRED"}
MAX_OUTPUT = 4 * 1024**2


class SignatureVerificationError(RuntimeError):
    """Package evidence is unsafe, incomplete, or inconsistent."""


@dataclass(frozen=True)
class SignatureEvidence:
    filename: str
    package_sha256: str
    signature_sha256: str
    signer_fingerprint: str
    primary_fingerprint: str
    trusted_master_certifications: tuple[str, ...]
    primary_valid: bool
    independent_valid: bool


@dataclass(frozen=True)
class SignatureVerificationReport:
    schema_version: int
    manifest_digest: str
    package_count: int
    unique_signers: tuple[str, ...]
    evidence: tuple[SignatureEvidence, ...]
    evidence_digest: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _regular(path: Path) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise SignatureVerificationError("verification input is not one private regular file")


def parse_fingerprints(path: Path) -> frozenset[str]:
    values = set()
    for line in path.read_text(encoding="ascii").splitlines():
        value = line.split(":", 1)[0].strip().upper()
        if len(value) != 40 or any(c not in "0123456789ABCDEF" for c in value):
            raise SignatureVerificationError("Arch trust file contains a malformed fingerprint")
        values.add(value)
    if not values:
        raise SignatureVerificationError("Arch trust file is empty")
    return frozenset(values)


def parse_valid_signature(output: str) -> tuple[str, str]:
    statuses = []
    for line in output.splitlines():
        if line.startswith("[GNUPG:] "):
            fields = line[9:].split()
            if fields:
                statuses.append(fields)
    if any(fields[0] in BAD_STATUS for fields in statuses):
        raise SignatureVerificationError("cryptographic signature was rejected")
    valid = [fields for fields in statuses if fields[0] == "VALIDSIG"]
    if len(valid) != 1 or len(valid[0]) < 11:
        raise SignatureVerificationError("exactly one valid signature was not proven")
    signer, primary = valid[0][1].upper(), valid[0][-1].upper()
    if any(len(value) != 40 for value in (signer, primary)):
        raise SignatureVerificationError("signature fingerprint is malformed")
    return signer, primary


def parse_master_certifications(output: str, trusted: frozenset[str]) -> tuple[str, ...]:
    certifications = set()
    for line in output.splitlines():
        fields = line.split(":")
        if len(fields) > 12 and fields[0] == "sig" and fields[1] == "!":
            issuer = fields[12].upper()
            if issuer in trusted:
                certifications.add(issuer)
    return tuple(sorted(certifications))


def trust_is_sufficient(primary: str, certifications: tuple[str, ...], trusted: frozenset[str]) -> bool:
    return primary in trusted or len(set(certifications) & trusted) >= 3


def _run(command: tuple[str, ...], *, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        command, shell=False, stdin=subprocess.DEVNULL, capture_output=True,
        timeout=60, env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    if len(result.stdout) > MAX_OUTPUT or len(result.stderr) > MAX_OUTPUT:
        raise SignatureVerificationError("verification tool output exceeded its bound")
    if result.returncode != 0:
        raise SignatureVerificationError("offline signature tool rejected an input")
    return result.stdout if binary else result.stdout.decode("utf-8", "strict")


def _write_exclusive(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise SignatureVerificationError("evidence write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def verify_fixed_acquisition(*, root: Path = ROOT) -> SignatureVerificationReport:
    manifest = parse_resolution_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.manifest_digest != AUTHORIZED_MANIFEST or len(manifest.packages) != 138:
        raise SignatureVerificationError("package manifest is not the authorized closed set")
    for path, expected in TRUST_INPUT_HASHES.items():
        _regular(path)
        if _sha256(path) != expected:
            raise SignatureVerificationError("installed Arch trust material changed")
    trusted, revoked = parse_fingerprints(TRUSTED), parse_fingerprints(REVOKED)
    try:
        os.mkdir(root, 0o700)
    except FileExistsError as error:
        raise SignatureVerificationError("verification root exists; refusing adoption") from error
    home = root / "gnupg"
    home.mkdir(mode=0o700)
    base = ("/usr/bin/gpg", "--batch", "--no-autostart", "--homedir", str(home))
    _run(base + ("--import", str(KEYRING)))
    evidence = []
    certification_cache: dict[str, tuple[str, ...]] = {}
    for item in manifest.packages:
        package, signature = PACKAGE_ROOT / item.filename, PACKAGE_ROOT / (item.filename + ".sig")
        _regular(package); _regular(signature)
        package_hash = _sha256(package)
        if package_hash != item.sha256:
            raise SignatureVerificationError("package bytes disagree with the authorized manifest")
        output = _run(base + ("--status-fd", "1", "--verify", str(signature), str(package)))
        signer, primary = parse_valid_signature(output)
        if signer in revoked or primary in revoked:
            raise SignatureVerificationError("package was signed by a revoked Arch identity")
        if primary not in certification_cache:
            checks = _run(base + ("--with-colons", "--check-sigs", primary))
            certification_cache[primary] = parse_master_certifications(checks, trusted)
        certifications = certification_cache[primary]
        if not trust_is_sufficient(primary, certifications, trusted):
            raise SignatureVerificationError("signer lacks sufficient current Arch master trust")
        evidence.append(SignatureEvidence(
            item.filename, package_hash, _sha256(signature), signer, primary,
            certifications, True, False,
        ))
    exported = _run(base + ("--export",), binary=True)
    assert isinstance(exported, bytes)
    keyring = root / "independent-keyring.gpg"
    _write_exclusive(keyring, exported)
    completed = []
    for item, first in zip(manifest.packages, evidence):
        package, signature = PACKAGE_ROOT / item.filename, PACKAGE_ROOT / (item.filename + ".sig")
        output = _run(("/usr/bin/gpgv", "--status-fd", "1", "--keyring", str(keyring), str(signature), str(package)))
        signer, primary = parse_valid_signature(output)
        if (signer, primary) != (first.signer_fingerprint, first.primary_fingerprint):
            raise SignatureVerificationError("independent verifier identified a different signer")
        completed.append(SignatureEvidence(**{**asdict(first), "independent_valid": True}))
    payload = {
        "schema_version": 1, "manifest_digest": manifest.manifest_digest,
        "package_count": len(completed), "unique_signers": sorted({x.primary_fingerprint for x in completed}),
        "evidence": [asdict(item) for item in completed],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    payload["evidence_digest"] = digest
    _write_exclusive(root / "signature-evidence.json", (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode())
    return SignatureVerificationReport(1, manifest.manifest_digest, len(completed), tuple(payload["unique_signers"]), tuple(completed), digest)


def main() -> int:
    report = verify_fixed_acquisition()
    print("APX offline package signature verification")
    print(f"Packages verified twice: {report.package_count}")
    print(f"Trusted signing identities: {len(report.unique_signers)}")
    print(f"Evidence digest: {report.evidence_digest}")
    print(f"Evidence: {ROOT / 'signature-evidence.json'}")
    print("Network/install/extract/execute/cleanup effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
