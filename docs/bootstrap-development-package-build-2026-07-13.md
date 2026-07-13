# APX Contracts Development Package Build — 2026-07-13

Status: unsigned same-Development-environment reproducibility evidence. This is
not independent-builder proof, production trust, installation approval, or a
functional APX bootstrap package.

## Frozen Input

- source revision: `c6f61ff7259fa71039c087023018731c6f3a774d`;
- commit time / `SOURCE_DATE_EPOCH`: `1783975292`;
- two independently exported Git archives;
- source archive size: 10,670,080 bytes;
- source archive SHA-256:
  `996440d4a0706babc5e714c8598cbfdff088a068c448698e03ad0c8628610f5e`;
- recipe SHA-256:
  `9b3d6e7828ae2fc47414d1bc6f51935255a04e457fc32f62b2e26c45d4af3a0c`;
- makepkg 7.1.0, fakeroot 1.37.2;
- package classification: `unsigned-development-only`.

The two Git archives were byte-identical before either accepted build.

## Detected Reproducibility Failure

The first attempt used two different absolute directories. Package sizes were
21,589 and 21,604 bytes and SHA-256 values differed. Inspection found the only
semantic input difference in `.BUILDINFO`: `builddir` and `startdir` contained
the two absolute paths, which also changed `.MTREE` and the compressed package.

That attempt is retained as negative evidence. APX does not call it
reproducible.

## Corrected Same-Environment Result

Two clean sequential builds used the canonical path
`/tmp/apx-contracts-reproducible-build`, regenerated identical source archives,
and froze `SOURCE_DATE_EPOCH`. The final packages matched byte for byte:

- filename: `apx-contracts-development-0.1.0.dev1-1-any.pkg.tar.zst`;
- size: 21,601 bytes;
- package SHA-256:
  `3895d89e34a95b38bc5559a49b87cd338725b3889a42122932fd2a0fe3fff76a`;
- `.PKGINFO` SHA-256:
  `b885549fd57064e68034c9ff62601677d8bf9575037d4072a94d471de0196d4f`;
- `.BUILDINFO` SHA-256:
  `0587600b524a338d7832da5af82664f96202d8e02aa83d9636c43dfbddc2ba55`;
- `.MTREE` SHA-256:
  `31456ea68b30095536a28117e3727e0cdfb77400da569c2d077c10226385291c`.

The archive contains only the three fixed Python validators, four fixed
documents, Apache-2.0 licence declaration, required directories, and Arch
metadata. It contains no executable APX command, service, hook, installer,
credential, source checkout, cache, or private key.

## Remaining Independent Proof

Both successful builds ran in the same Development Environment. `.BUILDINFO`
records its full installed-package inventory as well as the build path. The next
proof therefore requires two separately created, network-disabled builders from
one frozen builder image/manifest, exposing the same canonical internal path.
Only if their complete package and all four internal evidence digests agree may
the package contract classify the rebuild as an exact independent match.

The package remains only in temporary evidence storage and was not installed,
signed, copied into Hub, admitted, committed, or pushed.
