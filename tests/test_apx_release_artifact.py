from __future__ import annotations

from dataclasses import replace
from dataclasses import asdict
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_release_artifact as artifact
from tests.test_apx_release_candidate import valid_candidate


def members():
    return (
        artifact.ArchiveMember("etc", "directory", 0, 0o755, 0, 0, None, None),
        artifact.ArchiveMember("home", "directory", 0, 0o755, 0, 0, None, None),
        artifact.ArchiveMember("usr", "directory", 0, 0o755, 0, 0, None, None),
        artifact.ArchiveMember("usr/bin", "directory", 0, 0o755, 0, 0, None, None),
        artifact.ArchiveMember("usr/bin/apx", "regular", 12, 0o755, 0, 0, "a" * 64, None),
        artifact.ArchiveMember("usr/bin/apxcopy", "hardlink", 0, 0o755, 0, 0, None, "usr/bin/apx"),
        artifact.ArchiveMember("usr/bin/apxctl", "symlink", 0, 0o777, 0, 0, None, "apx"),
        artifact.ArchiveMember("var", "directory", 0, 0o755, 0, 0, None, None),
    )


def candidate_for(member_set=None, artifact_sha="d" * 64):
    member_set = members() if member_set is None else member_set
    return replace(
        valid_candidate(),
        artifact_member_count=len(member_set),
        artifact_sha256=artifact_sha,
        normalized_root_digest=artifact.normalized_root_digest(member_set),
    )


class ReleaseArtifactTests(unittest.TestCase):
    def test_valid_manifest_binds_candidate_and_normalized_tree(self) -> None:
        subject = artifact.build_artifact_manifest(candidate_for(), members())
        artifact.validate_artifact_manifest(subject)
        self.assertEqual(subject.member_count, len(members()))
        self.assertEqual(subject.total_regular_bytes, 12)
        self.assertEqual(len(subject.manifest_digest), 64)
        encoded = artifact.manifest_to_json(subject)
        self.assertEqual(artifact.parse_artifact_manifest_json(encoded), subject)

    def test_paths_duplicates_order_and_required_directories_fail(self) -> None:
        cases = (
            replace(members()[0], path="/etc"),
            replace(members()[0], path="etc/../host"),
            replace(members()[0], path="etc//x"),
            replace(members()[0], path="etc\x00x"),
        )
        for changed in cases:
            value = (changed,) + members()[1:]
            with self.subTest(path=changed.path):
                with self.assertRaises(artifact.ReleaseArtifactError):
                    artifact.validate_members(value)
        with self.assertRaises(artifact.ReleaseArtifactError):
            artifact.validate_members(members() + (members()[-1],))
        with self.assertRaises(artifact.ReleaseArtifactError):
            artifact.validate_members(tuple(reversed(members())))
        without_etc = tuple(item for item in members() if item.path != "etc")
        with self.assertRaisesRegex(artifact.ReleaseArtifactError, "required"):
            artifact.validate_members(without_etc)
        missing_parent = tuple(
            item for item in members() if item.path != "usr/bin"
        )
        with self.assertRaisesRegex(artifact.ReleaseArtifactError, "parent"):
            artifact.validate_members(missing_parent)

    def test_special_kinds_privileged_modes_and_wrong_shapes_fail(self) -> None:
        variants = (
            replace(members()[4], kind="device"),
            replace(members()[4], mode=0o4755),
            replace(members()[4], size=True),
            replace(members()[4], uid=-1),
            replace(members()[4], content_sha256=None),
            replace(members()[0], size=1),
            replace(members()[5], content_sha256="b" * 64),
        )
        for changed in variants:
            with self.subTest(changed=changed):
                with self.assertRaises(artifact.ReleaseArtifactError):
                    artifact._validate_member_shape(changed)

    def test_links_cannot_escape_and_hardlink_requires_regular_target(self) -> None:
        for target in ("../../../host", "", "../..", "/usr/bin/apx"):
            changed = replace(members()[5], link_target=target)
            with self.subTest(target=target):
                with self.assertRaises(artifact.ReleaseArtifactError):
                    artifact._validate_member_shape(changed)
        bad_hardlink = tuple(
            replace(item, link_target="etc") if item.path == "usr/bin/apxcopy" else item
            for item in members()
        )
        with self.assertRaisesRegex(artifact.ReleaseArtifactError, "hardlink"):
            artifact.validate_members(bad_hardlink)

        escaping_symlink = replace(members()[6], link_target="../../../host")
        with self.assertRaises(artifact.ReleaseArtifactError):
            artifact._validate_member_shape(escaping_symlink)

    def test_mutable_personal_identity_and_development_paths_fail(self) -> None:
        forbidden = (
            "etc/machine-id",
            "etc/hostname",
            "home/user/file",
            "root/token",
            "run/socket",
            "tmp/output",
            "var/lib/apx/metadata",
            "usr/src/.git/config",
            "opt/.codex/session",
        )
        for path in forbidden:
            changed = artifact.ArchiveMember(path, "regular", 1, 0o600, 0, 0, "b" * 64, None)
            candidate_members = tuple(sorted(members() + (changed,), key=lambda item: item.path))
            with self.subTest(path=path):
                with self.assertRaises(artifact.ReleaseArtifactError):
                    artifact.validate_members(candidate_members)

    def test_candidate_count_and_root_digest_must_match(self) -> None:
        with self.assertRaisesRegex(artifact.ReleaseArtifactError, "count"):
            artifact.build_artifact_manifest(
                replace(candidate_for(), artifact_member_count=1), members()
            )
        with self.assertRaisesRegex(artifact.ReleaseArtifactError, "root digest"):
            artifact.build_artifact_manifest(
                replace(candidate_for(), normalized_root_digest="e" * 64), members()
            )

    def test_json_rejects_unknown_missing_duplicate_and_member_extensions(self) -> None:
        manifest = artifact.build_artifact_manifest(candidate_for(), members())
        payload = asdict(manifest)
        payload["command"] = "extract-as-root"
        with self.assertRaises(artifact.ReleaseArtifactError):
            artifact.parse_artifact_manifest_json(json.dumps(payload))
        del payload["command"]
        del payload["artifact_sha256"]
        with self.assertRaises(artifact.ReleaseArtifactError):
            artifact.parse_artifact_manifest_json(json.dumps(payload))

        canonical = artifact.manifest_to_json(manifest).strip()
        duplicate = canonical[:-1] + ',"schema_version":1}'
        with self.assertRaises(artifact.ReleaseArtifactError):
            artifact.parse_artifact_manifest_json(duplicate)

        payload = asdict(manifest)
        payload["members"][0]["xattr"] = "security.capability"
        with self.assertRaises(artifact.ReleaseArtifactError):
            artifact.parse_artifact_manifest_json(json.dumps(payload))

    def test_exact_rebuilds_match_despite_different_candidate_identity(self) -> None:
        first = artifact.build_artifact_manifest(candidate_for(), members())
        second_candidate = replace(
            candidate_for(),
            candidate_id="candidate-" + "f" * 32,
            build_operation_id="build-" + "e" * 32,
        )
        second = artifact.build_artifact_manifest(second_candidate, members())
        result = artifact.compare_rebuilds(first, second)
        self.assertEqual(result.classification, "exact-match")
        self.assertEqual(result.issues, ())

    def test_any_tree_or_compressed_artifact_change_breaks_reproducibility(self) -> None:
        first = artifact.build_artifact_manifest(candidate_for(), members())
        changed_members = tuple(
            replace(item, content_sha256="c" * 64)
            if item.path == "usr/bin/apx" else item
            for item in members()
        )
        changed_tree = artifact.build_artifact_manifest(
            candidate_for(changed_members), changed_members
        )
        changed_archive = artifact.build_artifact_manifest(
            candidate_for(artifact_sha="e" * 64), members()
        )
        self.assertEqual(artifact.compare_rebuilds(first, changed_tree).classification, "mismatch")
        self.assertEqual(artifact.compare_rebuilds(first, changed_archive).classification, "mismatch")


if __name__ == "__main__":
    unittest.main()
