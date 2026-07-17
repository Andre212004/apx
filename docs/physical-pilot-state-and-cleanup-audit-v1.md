# APX Physical Pilot State and Cleanup Audit v1

Status: owner-run, read-only evidence handoff for the target-bound physical
development pilot. It inventories the host, Hub, and Development and prepares
a cleanup proposal. It does not authorize deletion, package removal, service
changes, quota changes, or an APX host update.

## Purpose and Current Checkpoint

The owner reported on 2026-07-17 that Phases 1 through 8 of
`physical-headless-development-handoff-v1.md` are complete and that Ollama was
installed inside Development without downloading a local model. The rest of
Phase 9 and Phase 10 are pending. This audit turns that report into reviewable
evidence and finds temporary installation material, duplicate clones, downloads,
caches, unexpected packages, services, listeners, and APX state that may need
later review.

The audit has two sessions:

1. collect and classify without changing the machine;
2. after repository review, execute only an exact separately approved cleanup
   plan and verify the result.

Never combine those sessions. Finding an object is not authority to remove it.

## Safety Rules for ChatGPT

Give this entire file to ChatGPT and begin with this instruction:

```text
Follow docs/physical-pilot-state-and-cleanup-audit-v1.md exactly. This is the
read-only evidence session. Do not delete, move, truncate, edit, install,
upgrade, remove, enable, disable, start, stop, restart, mount, unmount, snapshot,
restore, destroy, prune, vacuum, or change permissions, ownership, quotas,
users, services, packages, repositories, boot files, or APX state. Do not use
rm, rmdir, unlink, mv, pacman with a mutating option, systemctl with a mutating
verb, btrfs subvolume delete, btrfs qgroup destroy, journalctl vacuum options,
or any cleanup command. Do not print file contents from credential or secret
locations. Collect only the requested metadata, redact secrets, classify every
candidate, and stop with a proposed review plan. Unknown means preserve.
```

ChatGPT must stop if the machine identity, APX marker, expected Environment
names, or execution context differs. It must not adapt paths to make a command
work. Do not paste passwords, LUKS passphrases, tokens, cookies, private keys,
recovery codes, credential files, full environment-variable dumps, or command
histories into ChatGPT or GitHub.

Package names, file paths, ownership, modes, sizes, hashes of public scripts,
unit names, listeners, mount metadata, and redacted results are suitable
evidence.

## Step 1 — Establish the Host Context

Run from the physical host root recovery/bootstrap console, not from Hub or
Development:

```bash
id
hostnamectl --static
systemd-detect-virt
cat /sys/class/dmi/id/sys_vendor
cat /sys/class/dmi/id/product_name
cat /sys/class/dmi/id/board_name
test -f /etc/apx-physical-pilot && sed -n '1,20p' /etc/apx-physical-pilot
findmnt -no SOURCE,FSTYPE,OPTIONS -T /var/lib/apx
lsblk -e7 -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL
```

Expected identity is physical `LENOVO`, product `82JU`, board
`LNVNB161216`, hostname `apx-host`, and the documented pilot marker. Stop on a
mismatch. Do not run disk-repair or mount commands.

Record current APX status without changing lifecycle state:

```bash
apx status
apx environment list --json
machinectl list --no-legend
systemctl --failed --no-legend
systemctl list-units --type=service --state=running --no-legend
ss -lntup
```

Do not stop or start an Environment just to make the output look cleaner.

## Step 2 — Inventory Host Packages and Development Material

The steady-state host should remain minimal. Collect package lists:

```bash
pacman -Q
pacman -Qqe
pacman -Qqm
pacman -Qdtq
```

`pacman -Qdtq` reports possible orphan packages; it does not prove they are
unneeded. Preserve every result until dependency, APX bootstrap use, recovery
value, and ownership are reviewed.

Inventory the root account by metadata only:

```bash
find /root -xdev -mindepth 1 -maxdepth 2 -printf '%y %m %u:%g %s %TY-%Tm-%TdT%TH:%TM %p\n' | sort
du -x -h -d 2 /root 2>/dev/null | sort -h
find /root -xdev -type d -name .git -printf '%h\n' | sort
find /root -xdev -type f \( -name '*.iso' -o -name '*.img' -o -name '*.qcow2' -o -name '*.tar' -o -name '*.tar.zst' -o -name '*.pkg.tar.zst' -o -name '*.part' \) -printf '%s %TY-%Tm-%Td %p\n' | sort -n
```

Do not display dotfile or authentication-directory contents. Expected temporary
candidates may include `/root/apx-bootstrap` and the host `git` package, but
neither is removable until the applicable Phase 9 facts and all Phase 10 gates
pass. A deliberately deferred model is not itself a cleanup blocker.

Check temporary and cache locations without traversing pseudo-filesystems:

```bash
du -x -h -d 2 /var/cache /var/tmp /tmp 2>/dev/null | sort -h | tail -120
find /var/tmp /tmp -xdev -mindepth 1 -maxdepth 2 -printf '%y %u:%g %s %TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null | sort
journalctl --disk-usage
coredumpctl list --no-pager
```

Logs, caches, and crash dumps remain preserved during this audit.

## Step 3 — Inventory APX Host-Owned State

Record topology, identities, sizes, and registrations without dumping all file
contents:

```bash
find /var/lib/apx -xdev -mindepth 1 -maxdepth 3 -printf '%y %m %u:%g %s %p\n' | sort
du -x -h -d 3 /var/lib/apx 2>/dev/null | sort -h
find /var/lib/apx/environments -mindepth 2 -maxdepth 2 -name registration.json -type f -print -exec python -m json.tool {} \;
btrfs subvolume list -p -q -u /var/lib/apx
btrfs quota status /var/lib/apx
findmnt -R /var/lib/apx
```

If qgroup visibility is incomplete through `/var/lib/apx`, report that fact.
Do not create a top-level mount during the audit. The reviewed quota recovery
script owns that special operation.

Collect plans, journals, snapshots, archives, quarantine, catalogue, and
releases as names and metadata only:

```bash
for area in plans journal snapshots archives quarantine catalogue releases; do
  printf '\n[%s]\n' "$area"
  find "/var/lib/apx/$area" -xdev -mindepth 1 -maxdepth 2 -printf '%y %m %u:%g %s %TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null | sort
done
```

Age alone does not make a plan, journal entry, snapshot, archive, or release
junk. It may be required for recovery or provenance.

## Step 4 — Inspect Hub

If Hub is already running, use it as observed. If it is stopped, report that
and defer its inside view; do not start it during the read-only session.

From the host, when `apx-hub` is already running:

```bash
machinectl shell root@apx-hub /bin/bash -lc '
set -u
printf "[identity]\n"; id; hostnamectl --static
printf "[packages]\n"; pacman -Q
printf "[explicit packages]\n"; pacman -Qqe
printf "[running services]\n"; systemctl list-units --type=service --state=running --no-legend
printf "[listeners]\n"; ss -lntup
printf "[homes]\n"; find /home -xdev -mindepth 1 -maxdepth 3 -printf "%y %m %u:%g %s %p\n" | sort
printf "[development tools]\n"
for command in git gh gcc cc make node npm codex ollama qwen; do command -v "$command" 2>/dev/null && printf "UNEXPECTED_COMMAND %s\n" "$command"; done
printf "[repositories]\n"; find /root /home -xdev -type d -name .git -printf "%h\n" 2>/dev/null | sort
printf "[large files]\n"; find /root /home /var -xdev -type f -size +100M -printf "%s %p\n" 2>/dev/null | sort -n
'
```

Expected Hub findings are the bounded APX client and role-appropriate state.
Git, GitHub CLI, compilers, Node.js, npm, Codex, Ollama, Qwen Code, model files,
source repositories, credentials, and general development downloads are review
failures. They are still preserved until an exact cleanup plan exists.

## Step 5 — Inspect Development

If Development is already running, run the following from the host. If it is
stopped, report that and defer the inside view rather than starting it.

```bash
machinectl shell root@apx-development /bin/bash -lc '
set -u
printf "[identity]\n"; id; hostnamectl --static
printf "[filesystem]\n"; df -h / /home/apx; findmnt
printf "[packages]\n"; pacman -Q
printf "[explicit packages]\n"; pacman -Qqe
printf "[orphans-review-only]\n"; pacman -Qdtq || true
printf "[running services]\n"; systemctl list-units --type=service --state=running --no-legend
printf "[listeners]\n"; ss -lntup
printf "[repository locations]\n"; find /root /home -xdev -type d -name .git -printf "%h\n" 2>/dev/null | sort
printf "[large files]\n"; find /root /home /var -xdev -type f -size +100M -printf "%s %u:%g %p\n" 2>/dev/null | sort -n
printf "[downloads and build remnants]\n"; find /root /home/apx /var/tmp /tmp -xdev -type f \( -name "*.part" -o -name "*.iso" -o -name "*.img" -o -name "*.qcow2" -o -name "*.pkg.tar.zst" -o -name "core.*" \) -printf "%s %TY-%Tm-%Td %p\n" 2>/dev/null | sort -n
printf "[APX boundary]\n"; test ! -e /run/apx/executor.sock && echo executor_socket_absent || echo UNEXPECTED_EXECUTOR_SOCKET
command -v apx >/dev/null && echo UNEXPECTED_APX_COMMAND || echo apx_command_absent
'
```

As the `apx` user, collect repository state without showing credentials:

```bash
machinectl shell root@apx-development /bin/bash -lc '
su - apx -c '\''
cd /home/apx/work/apx || exit 1
git status --short --branch
git remote -v
git log -5 --oneline --decorate
git fsck --no-dangling
gh auth status
codex login status
du -x -h -d 2 /home/apx 2>/dev/null | sort -h | tail -100
'\''
'
```

Authentication status is suitable; token or credential contents are not.
Multiple clones, package build trees, large downloads, tool caches, and model
directories are review candidates, not automatic deletion targets.

Collect the reported package-only Ollama state explicitly. These commands do
not start the service or download a model:

```bash
machinectl shell root@apx-development /bin/bash -lc '
printf "[Ollama and Qwen packages]\n"
pacman -Q ollama qwen-code 2>&1 || true
printf "[Ollama command and account]\n"
command -v ollama || true
getent passwd ollama || true
printf "[Ollama service state]\n"
systemctl is-enabled ollama.service 2>&1 || true
systemctl is-active ollama.service 2>&1 || true
systemctl show ollama.service -p FragmentPath -p User -p Group -p ExecStart -p Environment --no-pager 2>&1 || true
printf "[Ollama listeners]\n"
ss -ltnp | awk '\''NR == 1 || /:11434([[:space:]]|$)/'\''
printf "[Ollama model list]\n"
ollama list 2>&1 || true
printf "[Known Ollama data locations: metadata only]\n"
for path in /var/lib/ollama /usr/share/ollama /home/apx/.ollama /root/.ollama; do
  if test -e "$path"; then
    find "$path" -xdev -mindepth 0 -maxdepth 3 -printf "%y %m %u:%g %s %TY-%Tm-%TdT%TH:%TM %p\n" 2>/dev/null | sort
    du -x -h -d 3 "$path" 2>/dev/null | sort -h
  fi
done
'
```

Do not use `ollama pull`, `ollama run`, `systemctl start`, or `systemctl enable`
during the audit. `Environment=` output must be checked before sharing; redact
any value if it unexpectedly contains a token or credential. Ordinary listener
and model-directory settings may remain visible.

## Step 6 — Phase 9 and Phase 10 Readiness

Record the current partial Phase 9 state without attempting to complete it:

- v3 quota recovery completion and verified 16/8 GiB Development limits;
- external-SSD storage design if model data will live there;
- exact Ollama package version, service enablement/activity, listener, service
  user, configured model directory, and directory size inside Development;
- `ollama list` output proving whether zero models or exact admitted models are
  present;
- partial manifests, blobs, or downloads reported as metadata only;
- Qwen Code presence or absence;
- any listener bound only to Development loopback;
- Hub and host unable to reach any Development Ollama listener.

If no model is installed, model response, persistence, and model stop/restart
checks are `not-applicable`, not failed. The service/process teardown check
still applies if Ollama is enabled or running. Do not download a model to make
the audit complete.

Before Phase 10 cleanup, additionally prove:

- Development repository, GitHub authentication, and Codex survive a full
  stop/start cycle;
- Hub contains no Development-only command, repository, credential, model,
  service, cache, or endpoint;
- the host contains no development service and only the documented temporary
  bootstrap clone/package candidates;
- APX reports no uncertain operation or failed unit;
- expected registrations, release identities, subvolumes, mounts, and qgroups
  remain consistent;
- recovery and the GitHub source copy do not rely on the proposed removal.

The external SSD must not be attached as a shared writable host/Hub/Development
path by convenience. Its exact device identity, encryption, mount owner,
disconnect behavior, model integrity, backup, quota/resource accounting, and
Environment visibility require a separate repository design before use.

## Step 7 — Required Classification Report

ChatGPT must return four tables:

1. `Expected and required`: object, location, owner, purpose, evidence;
2. `Expected temporary`: object, why temporary, prerequisite before removal;
3. `Unexpected review candidate`: object, observed facts, possible origin,
   consequence of removal, missing evidence;
4. `Preserve or unknown`: object, uncertainty, evidence needed.

It must then report:

- which handoff phase is actually evidenced;
- every failed or unavailable observation;
- whether Phase 9 is ready, blocked, or deliberately deferred;
- whether Phase 10 remains blocked;
- an exact proposed cleanup plan with one line per object, but no cleanup
  commands yet;
- an exact post-cleanup verification plan;
- sanitized output suitable for a dated repository evidence file.

Any credential exposure, identity mismatch, unhealthy quota state, unexpected
executor access, unknown APX object, active uncertain operation, or unexplained
host/Hub development tool blocks cleanup.

## Separately Approved Cleanup Session

This section is not standing authorization. Begin it only after the collected
report has been reviewed in Development, the repository contains an exact
target list and rollback/recovery analysis, and the owner explicitly approves
that list.

The cleanup ChatGPT must re-observe every target immediately before action,
refuse identity drift, execute one bounded group at a time, and verify after
each group. It must never broaden a pathname, wildcard, package list, or APX
scope. The initial handoff identifies only two possible Phase 10 objects:
`/root/apx-bootstrap` and the temporary host `git` package. Additional
candidates require their own reviewed instructions.

After approved cleanup, repeat Steps 1 through 6, run the APX status and
repository checks appropriate to the change, record exactly what was removed,
state whether recovery remains possible, and preserve every uncertain object.
