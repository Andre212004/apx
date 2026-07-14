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

## Independent Builder Proof

The follow-up proof used two separately created and removed rootless containers,
both with networking disabled and the same canonical guest-visible build path.
Their frozen inputs were:

- official Arch base manifest:
  `sha256:9edcc183d2505745a1da7a18bf12833dde174734610c72a5978031191504af1f`;
- builder image ID:
  `72a4a5f85fda5b54cb8ebf574b5d28b3db2a88a94f25d22daa0a8f913e930316`;
- builder manifest digest:
  `sha256:368cae87819b7d0aa69e3c448b431fe20fe744328405d80c88db8c46ae279007`;
- cached Arch `fakeroot` SHA-256:
  `f823c52c1450bf59a7fb493564793c61d7827fcba55524b0f5cd8ef41535a823`;
- cached Arch `mpdecimal` SHA-256:
  `8679f71ed9a982c91883adfaaf0f87a1b74d92d4060283180c4a105a6c7afb19`;
- cached Arch `python` SHA-256:
  `fda7dc7b67bd316a0e6a18164ffd122599458f4f9736caa0c35a9eb649bade8d`.

Both containers completed with no network and produced byte-identical outputs:

- package size: 16,109 bytes;
- package SHA-256:
  `9d6e53007bc56e8a9105f4ff65c14097dbec13aa8b0b4c7ddb70912b01b012fd`;
- `.PKGINFO` SHA-256:
  `b885549fd57064e68034c9ff62601677d8bf9575037d4072a94d471de0196d4f`;
- `.BUILDINFO` SHA-256:
  `9adb38dae73d117f3e031fba2d15a68b4b6b4e56ebf9d1ebe2c03657c0ebd591`;
- `.MTREE` SHA-256:
  `a29837ccf71166b6037de753196d3aa57b59a2cdaab745e40cc4828b7639a650`.

A third network-disabled disposable container installed that exact package after
disabling the base image's deliberate documentation `NoExtract` rule. Pacman
reported 16 total entries and zero altered files; all eight payload files were
present and the three Python modules imported with their fixed v1 identities.

This closes independent reproducibility and disposable installation for the
non-functional contracts package. It does not promote it to the production APX
bootstrap package. The package remains only in temporary evidence storage and
was not signed, copied into Hub, admitted, pushed, or installed on the host.
