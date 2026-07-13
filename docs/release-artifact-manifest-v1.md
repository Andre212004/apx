# APX Release Artifact Manifest v1

Status: closed pure contract for a headless Hub/root artefact. It validates
metadata only; it does not open, extract, mount, execute, sign, admit, or install
an archive.

## Member Model

Every archive member has exactly:

- normalized relative UTF-8 path;
- kind: `directory`, `regular`, `symlink`, or `hardlink`;
- byte size;
- permission mode;
- numeric owner and group;
- SHA-256 for regular content only;
- link target for links only.

Paths are Unicode NFC, printable, relative, and free from empty, `.` or `..`
segments. Members are unique and sorted. Special files, devices, FIFOs,
sockets, extended caller fields, set-user-ID/set-group-ID bits, and identifiers
outside the v1 bounds are rejected.

Symlinks are checked lexically without following them on the host. Relative and
container-root absolute targets may be represented only when normalization
stays within the future Environment root. Hardlinks must point to a regular
member through its canonical archive-root-relative path in the same manifest.

## Sanitization Boundary

The first manifest forbids mutable or personal paths including machine identity,
hostname, APX state, runtime state, temporary contents, live homes, root-home
contents, private key stores, and Development/Codex/Git state. `home`, `tmp`,
`run`, and similar empty structural directories may exist, but their mutable
contents cannot be published in a release.

Content scanning, package ownership, capabilities/xattrs, service policy,
password locking, and semantic configuration checks remain separate verifier
evidence. Passing this manifest cannot by itself admit a release.

## Identities and Reproducibility

The normalized root digest covers the complete canonical ordered member list.
The manifest additionally binds candidate identity, compressed artefact digest,
member count, and total regular-file bytes.

Two independent builds are an exact reproducibility match only when their
member lists, normalized root digests, compressed artefact digests, counts, and
byte totals agree. Candidate/build-operation IDs may differ and are not used to
hide output differences.

## Bounds

- at most 500,000 members;
- at most 16 GiB total regular-file bytes;
- paths and link targets at most 4096 encoded bytes;
- UID/GID from 0 through 65,535;
- regular file size bounded by the aggregate limit;
- serialized manifest at most 64 MiB.

The future raw archive reader must independently impose compressed and expanded
streaming limits, reject duplicate headers and sparse/decompression tricks, and
compare every observed member against this manifest before publication.
