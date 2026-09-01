from dataclasses import replace
import hashlib
import io
from pathlib import Path
import sys
import tarfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_physical_update_artifact as artifact
from tests.test_apx_physical_update import candidate as base_candidate


CONTENT = b"#!/usr/bin/env python3\nprint('safe fixture')\n"


def manifest() -> artifact.PhysicalUpdateArtifactManifest:
    base = base_candidate()
    return artifact.PhysicalUpdateArtifactManifest(
        1,
        base.profile,
        base.source_revision,
        base.parent_revision,
        ("host-runtime",),
        (
            artifact.PhysicalUpdateArtifactMember(
                "host-runtime", "components/host-runtime", len(CONTENT), 0o755,
                hashlib.sha256(CONTENT).hexdigest(),
            ),
        ),
    )


def tar_bytes(subject=None, *, extra=False, symlink=False, mtime=0) -> bytes:
    subject = manifest() if subject is None else subject
    manifest_bytes = artifact.manifest_to_bytes(subject)
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        info = tarfile.TarInfo("manifest.json")
        info.size, info.mode, info.uid, info.gid, info.mtime = len(manifest_bytes), 0o600, 0, 0, mtime
        archive.addfile(info, io.BytesIO(manifest_bytes))
        component = tarfile.TarInfo("components/host-runtime")
        component.size, component.mode, component.uid, component.gid, component.mtime = len(CONTENT), 0o755, 0, 0, mtime
        if symlink:
            component.type, component.linkname, component.size = tarfile.SYMTYPE, "/usr/bin/apx", 0
            archive.addfile(component)
        else:
            archive.addfile(component, io.BytesIO(CONTENT))
        if extra:
            item = tarfile.TarInfo("commands/install.sh")
            item.size, item.mode, item.uid, item.gid, item.mtime = 1, 0o755, 0, 0, 0
            archive.addfile(item, io.BytesIO(b"x"))
    return output.getvalue()


def candidate_for(data: bytes, subject=None):
    subject = manifest() if subject is None else subject
    return replace(
        base_candidate(), components=("host-runtime",), artifact_sha256=hashlib.sha256(data).hexdigest(),
        artifact_bytes=len(data), member_manifest_digest=hashlib.sha256(artifact.manifest_to_bytes(subject)).hexdigest(),
        member_count=2,
    )


class PhysicalUpdateArtifactTests(unittest.TestCase):
    def test_exact_closed_artifact_is_inspected_without_extraction(self) -> None:
        data = tar_bytes()
        evidence = artifact.inspect_artifact(data, candidate_for(data))
        self.assertEqual(evidence.component_digests, (("host-runtime", hashlib.sha256(CONTENT).hexdigest()),))
        self.assertEqual(evidence.member_count, 2)

    def test_manifest_round_trip_is_canonical_and_duplicate_safe(self) -> None:
        encoded = artifact.manifest_to_bytes(manifest())
        self.assertEqual(artifact.parse_manifest_bytes(encoded), manifest())
        duplicate = encoded[:-2] + b',"schema_version":1}\n'
        with self.assertRaises(artifact.PhysicalUpdateArtifactError):
            artifact.parse_manifest_bytes(duplicate)
        with self.assertRaisesRegex(artifact.PhysicalUpdateArtifactError, "canonical"):
            artifact.parse_manifest_bytes(encoded.replace(b'":', b'" :', 1))

    def test_candidate_artifact_manifest_and_component_identity_are_all_bound(self) -> None:
        data = tar_bytes()
        original = candidate_for(data)
        cases = (
            replace(original, artifact_bytes=len(data) - 1),
            replace(original, artifact_sha256="0" * 64),
            replace(original, member_manifest_digest="0" * 64),
            replace(original, member_count=3),
            replace(original, components=("hub-client",)),
        )
        for changed in cases:
            with self.subTest(changed=changed):
                with self.assertRaises((artifact.PhysicalUpdateArtifactError, ValueError)):
                    artifact.inspect_artifact(data, changed)

    def test_links_extra_members_mutable_metadata_and_wrong_content_fail(self) -> None:
        variants = (
            tar_bytes(extra=True),
            tar_bytes(symlink=True),
            tar_bytes(mtime=1),
        )
        for data in variants:
            with self.subTest(size=len(data)):
                with self.assertRaises(artifact.PhysicalUpdateArtifactError):
                    artifact.inspect_artifact(data, candidate_for(data))
        changed = replace(manifest().members[0], sha256="0" * 64)
        subject = replace(manifest(), members=(changed,))
        data = tar_bytes(subject)
        with self.assertRaisesRegex(artifact.PhysicalUpdateArtifactError, "content"):
            artifact.inspect_artifact(data, candidate_for(data, subject))

    def test_manifest_rejects_paths_modes_sizes_revisions_and_component_drift(self) -> None:
        member = manifest().members[0]
        cases = (
            replace(manifest(), source_revision=manifest().parent_revision),
            replace(manifest(), components=("host-runtime", "host-runtime")),
            replace(manifest(), members=(replace(member, path="/usr/bin/apx"),)),
            replace(manifest(), members=(replace(member, mode=0o4755),)),
            replace(manifest(), members=(replace(member, bytes=0),)),
        )
        for changed in cases:
            with self.subTest(changed=changed):
                with self.assertRaises(artifact.PhysicalUpdateArtifactError):
                    artifact.validate_manifest(changed)


if __name__ == "__main__":
    unittest.main()
