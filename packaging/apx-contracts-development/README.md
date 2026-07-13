# Building `apx-contracts-development`

This recipe builds only the unsigned, non-functional contract package described
in `docs/bootstrap-development-package-v1.md`. It never builds the production
APX bootstrap package and must not be installed as though APX were functional.

The source is the exact local Git revision
`c6f61ff7259fa71039c087023018731c6f3a774d`. Prepare it without network access:

```text
git archive --format=tar \
  --prefix=apx-c6f61ff7259fa71039c087023018731c6f3a774d/ \
  --output=apx-c6f61ff7259fa71039c087023018731c6f3a774d.tar \
  c6f61ff7259fa71039c087023018731c6f3a774d
```

The expected source archive SHA-256 is
`996440d4a0706babc5e714c8598cbfdff088a068c448698e03ad0c8628610f5e`.
Build with `SOURCE_DATE_EPOCH=1783975292`, the canonical build path
`/tmp/apx-contracts-reproducible-build`, network disabled, and the pinned
recipe. An independently created builder must reproduce that guest-visible path
and the complete frozen tool/package inventory recorded by `.BUILDINFO`.
Repeat the complete archive and build process, then compare the final package,
`.PKGINFO`, `.BUILDINFO`, `.MTREE`, and member-manifest SHA-256 values.

No package output belongs in Git. Failed or differing builds remain untrusted
evidence in their separate temporary build directories.
