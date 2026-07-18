# Temporary Root-Host Development Mode v1

Status: owner-approved repository preparation for a temporary experimental
mode on the disposable Lenovo physical pilot. This is not active merely because
this document exists.

## Plain-language purpose

Temporarily run Git, GitHub CLI, and Codex as `root@apx-host` so Codex can see
the Host, Hub, Development, and APX test Environments and automate physical
tests. Remove the temporary development mode completely when the work ends, or
reinstall Arch if complete removal cannot be proved.

This is a development-method exception. It is not the APX production design and
must never be copied into a release, base, Hub, or Environment template.

## What access means

Root Codex has technical power to change or destroy the entire machine. During
this mode it may inspect and modify the Host, Hub, Development, APX runtime, and
clearly named disposable test Environments when needed for repository work.

Standing permission is narrower than technical access:

- Codex may create, start, stop, modify, and destroy only disposable test
  Environments that it created and recorded itself;
- changing or destroying Hub or Development requires fresh owner approval;
- disk partitioning, formatting, encryption changes, Arch reinstallation,
  bootloader changes, and broad cleanup require fresh owner approval;
- credentials must never be printed, committed, copied into Hub, or copied into
  an Environment;
- uncertainty stops destructive work but does not stop read-only diagnosis.

## Enable the mode

Run only from the physical `root@apx-host` console after this exact repository
revision is available there. Do not run from Hub or Development.

```bash
cd /root/apx-bootstrap
git fetch origin master
git show origin/master:scripts/physical-pilot/prepare-root-host-development-mode-v1.sh > /tmp/prepare-root-host-development-mode-v1.sh
chmod 700 /tmp/prepare-root-host-development-mode-v1.sh
sed -n '1,260p' /tmp/prepare-root-host-development-mode-v1.sh
bash /tmp/prepare-root-host-development-mode-v1.sh
rm /tmp/prepare-root-host-development-mode-v1.sh
```

The helper refuses a different hostname, virtual machine, Lenovo identity, APX
marker, or missing APX runtime. It records a small baseline under
`/root/apx-host-development-mode-v1/evidence`, installs missing `git` and
`github-cli` packages, creates one dedicated checkout at
`/root/apx-host-development-mode-v1/apx`, and visibly displays the downloaded
official Codex installer before a second confirmation.

Authentication remains interactive:

```bash
gh auth login
codex login --device-auth
gh auth status
codex login status
cd /root/apx-host-development-mode-v1/apx
codex
```

Do not paste tokens or authentication files into ChatGPT. The standalone
installer URL and device authentication command follow the already reviewed
headless route used by the physical pilot. Recheck the official Codex
documentation if either command reports that it has changed.

## Prompt to paste into root Codex

```text
You are running temporarily as root on the disposable physical APX pilot.
Read AGENTS.md, PROJECT_STATE.md, CURRENT_HANDOFF.md, and
docs/temporary-root-host-development-mode-v1.md completely before acting.

The owner has approved this temporary root-host development mode so you can
automate APX development and physical testing across the Host, Hub, Development,
and disposable test Environments. This is experimental and not production.

Start by confirming the fixed Lenovo identity, APX marker, repository branch,
remote, working-tree state, APX status, active Environments, failed units,
mounts, and Btrfs quota health. Reconcile the dated physical audit with
PROJECT_STATE.md and CURRENT_HANDOFF.md before relying on its conclusions.

Work autonomously on repository changes and repeatable tests. Prefer scripts
and captured evidence over asking me to type long command sequences. Before
each physical test, explain briefly what it changes and how recovery works.
Stop on identity drift, uncertain APX state, unhealthy storage, unexpected
mounts, exposed credentials, or an unclean repository.

You may create, modify, start, stop, and destroy clearly named disposable test
Environments that you create and record yourself. You may inspect and test Hub
and Development. Ask me for fresh explicit approval before changing or
destroying Hub or Development, touching disk layout or encryption, changing the
bootloader, reinstalling Arch, or performing broad cleanup. Never treat root
access as production architecture or copy Codex/Git credentials into APX roles.

Keep repository documentation factual. Clearly distinguish observed physical
evidence, repository implementation, intended architecture, and experiments.
Run relevant tests after every change. Do not commit or push unless I explicitly
ask in that chat. Maintain an exact inventory of everything this temporary mode
adds so it can later be removed completely.

First task: review the current physical state, reconcile the 2026-07-17 audit,
and propose the smallest automated sequence that completes the remaining Phase
9 evidence and determines whether Phase 10 is ready. Do not clean anything yet.
```

## Operating rules

Keep every host-development change in the dedicated checkout. Use names that
begin with `codex-test-` for disposable Environments. Before creating one,
record its intended role and cleanup check. After destroying one, prove its
registration, processes, units, mounts, subvolumes, qgroups, plans, and runtime
state are absent or intentionally retained.

Commit and push only after the owner explicitly requests it. Never use the live
Hub as source, template, build directory, credential store, or development
checkout.

## Exit and complete removal

Do not improvise cleanup and do not remove the mode while it contains unpushed
work. The eventual exit is a separate session:

1. stop new experiments and obtain a clean, synchronized repository;
2. inventory packages, Codex executable paths, `/root/.codex`, root
   configuration, caches, authentication, shell changes, temporary files, the
   dedicated checkout, and the baseline recorded by the helper;
3. compare that inventory with the pre-mode audit and package database;
4. prepare an exact path-by-path and package-by-package removal plan;
5. preserve APX state, recovery material, logs needed for diagnosis, and every
   unknown object;
6. obtain fresh owner approval for the exact removal list;
7. remove one bounded group at a time and verify APX after each group;
8. prove that Codex, its credentials/state, GitHub CLI, the temporary checkout,
   and any packages installed only for this mode are absent;
9. prove Hub, Development, APX registrations, releases, journals, mounts,
   subvolumes, and qgroups still match the accepted final state;
10. reinstall Arch using the separately approved physical installer if complete
    removal or trustworthy final state cannot be proved.

The preparation helper deliberately contains no cleanup command. Installation
paths and package dependencies must be observed on the actual host before an
exact destructive cleanup helper can safely be written.
