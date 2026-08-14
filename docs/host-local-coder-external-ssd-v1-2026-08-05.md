# Host-local coder and external SSD v1 — 2026-08-05

Status: owner-authorized physical implementation completed and locally proved,
except for deliberate omission of an unsafe live cable-removal test.

## Owner decision and architectural deviation

The owner explicitly selected the connected Samsung 870 QVO 1 TB as dedicated
local-model storage, authorized destruction of all previous content, and chose
a Host-resident coding model that becomes available only while that exact SSD
is connected. This supersedes the earlier Development-only placement in
`external-development-model-storage-v1.md` for this physical pilot.

This is a conscious temporary deviation from APX's Environment-local
application rule. The model runtime, GPU libraries and Qwen Code executable are
Host packages. The model weights are on the external SSD. The API is Host
loopback only and is not exposed to the Hub, physical network or a workload
Environment. A later typed bridge or an Environment-owned runtime is required
before Development can consume it without moving the authority boundary.

## Physical preflight and destructive result

The stable physical identity is retained in the target-bound adapter rather
than repeated as a generic device path. The observed device was a Samsung SSD
870 QVO 1 TB, 1,000,204,886,016 bytes, connected through USB/SATA. It was the
external `/dev/sda`; the APX system remained the distinct internal 512 GB NVMe.
The previous single NTFS partition was not mounted and had no open users.

SMART reported `PASSED`, zero reallocated sectors, zero program/erase failures,
zero uncorrectable errors and no logged device errors. The owner-authorized
operation then removed the DOS/NTFS layout and created one GPT partition named
`APX_MODEL_STORE`. The resulting storage stack is:

```text
exact Samsung by-id identity
  -> one GPT Linux-LUKS partition
  -> LUKS2 APX_MODEL_STORE
  -> TPM2 automatic unlock bound to SHA-256 PCR 7
  -> Btrfs APX_MODEL_STORE
  -> /var/lib/apx/model-store
  -> ollama/ owned only by the ollama service account
```

The LUKS initialization key existed only as a mode-0600 temporary file under
`/run`, was replaced by the TPM2 token, was destroyed, and its keyslot was
removed. There is no password or recovery-key copy on the Host, SSD or
repository. This is deliberate because the SSD contains only replaceable
public model artifacts. If TPM or PCR-7 recovery fails after firmware or Secure
Boot changes, recovery is to recreate this model store and download the model
again; the volume is not a unique-data backup.

## Exact automatic activation

`apx-model-store-v1.py` validates the stable by-id path, physical model, serial,
exact byte size, partition UUID, LUKS UUID, filesystem UUID and filesystem type
before mounting anything. It refuses a mismatch. The mount is private under
`/var/lib/apx`, read-only during normal inference, with `nosuid`, `nodev`,
`noexec`, `noatime`, Zstd compression, SSD mode and asynchronous discard. The
unmounted Host directory is root-owned mode `000`, preventing an Ollama race
from silently writing model data onto the internal Host filesystem.

The udev rule requests `apx-model-store-v1.service` only when the exact
partition appears and also requests the Ollama unit for automatic model startup
on physical insertion. The store service itself is bound to the corresponding
systemd device unit, unlocks through the TPM and mounts independently.
Ollama is part of the store lifecycle, so a normal service stop first stops the
model server, unmounts the filesystem and closes LUKS. The unit is deliberately
not enabled as an unconditional boot service; device discovery is its trigger.

The Hub now has separate model-power and SSD-mount controls backed by an
authenticated, fixed-operation Unix socket. The first starts or stops only
Ollama while leaving the read-only SSD mounted. The second mounts the admitted
SSD without starting the model, or uses a second-click confirmation to stop
Ollama, synchronize, unmount Btrfs and close LUKS. It reports `SSD OK` only
after all three are inactive. Physical reinsertion still starts both services
automatically. The
controller accepts only the exact official Hub peer and the operations
`status`, `model-start`, `model-stop`, `storage-activate` and `safe-detach`; it
cannot execute arbitrary Host commands. Future Hub launches use the normal
leased `/run` binding. The
already-running Hub receives the same authenticated service through its
root-owned live bridge and an Environment-owned read-only client, so the
control is operational now without restarting the Hub.

Unexpected cable removal remains a hardware failure, but inference no longer
writes to the SSD and the device-bound unit still stops Ollama when systemd
observes loss. This substantially reduces the corruption window; it cannot
protect against electrical or USB-bridge failure. No deliberate live cable
removal was performed.

## Runtime and model selection

The Host packages are the official signed Arch packages for Ollama, its Vulkan
backend, AMD RADV, NVIDIA NVK, Qwen Code and SMART tools. Ollama listens only on
`127.0.0.1:11434`, permits one loaded model and one parallel request, uses a
32,768-token operating context, Flash Attention and an 8-bit KV cache, and has
cloud access disabled. GPU discovery selected the discrete RTX 3060 Laptop GPU
through Vulkan/NVK with about 5.4 GiB available; the integrated AMD GPU was not
selected.

The selected daily model is Ollama `qwen3-coder:30b`, an Apache-2.0 30B
mixture-of-experts coding model with about 3.3B parameters active per token and
an approximately 19 GB artifact. It is the strongest reviewed coding-agent
candidate that fits the machine's 28 GiB RAM with a useful context. The newer
Qwen3-Coder-Next has stronger agentic claims but its smallest official GGUF is
48.4 GB before context memory, so it would page heavily and is not admitted as
the daily model on this hardware.

Qwen Code is configured system-wide for the local OpenAI-compatible endpoint,
telemetry and self-update disabled, a ten-minute request timeout, one retry and
confirmation-based operation. `/usr/local/bin/apx-local-code` refuses to launch
unless the exact model-store and APX Ollama services are healthy. It never adds
an unrestricted or `--yolo` mode. The owner starts it from the intended source
checkout with:

```text
apx-local-code
```

Local inference does not make generated code trusted. Host-root Qwen Code can
request powerful file and shell actions; the owner must review every request,
diff and test just as with any untrusted implementation proposal.

## Physical evidence

Ollama acquired and verified `qwen3-coder:30b`. The served model ID is
`06c1097efce0`; the exact Ollama manifest SHA-256 is
`06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca`.
The principal model blob is 18,556,688,736 bytes with digest
`1194192cf2a187eb02722edcc3f77b11d21f537048ce04b67ccf8ba78863006a`.
The complete observed Ollama directory uses 18,556,701,475 bytes and has no
partial download. The manifest also binds the Apache-2.0 licence, parameters
and configuration blobs.

A direct 32K-context request returned exactly `APX_LOCAL_OK`. Cold load took
54.87 seconds and the five-token response ran at 8.35 tokens/s. Ollama reported
a 20 GB runtime split of 78% CPU and 22% GPU: about 16,151.7 MiB of CPU-mapped
weights, 2,494.4 MiB of Vulkan model data, 1,632 MiB of GPU KV cache and 273.6
MiB of GPU compute buffer. The service peak observed during the agent tests was
17.6 GiB; the Host remained healthy without swap.

Qwen Code reached the local OpenAI-compatible endpoint and returned exactly
`QWEN_CODE_LOCAL_OK`. The test also quantified the limitation: its normal full
tool prompt is about 9,467 tokens and cold preparation on this CPU/GPU split is
roughly ten minutes. A restricted 4,295-token smoke profile was cached and then
answered in 4.99 seconds. The model remains loaded for 30 minutes after use to
retain useful session and prompt-cache responsiveness. This is capable local
continuity, not Codex-equivalent latency or quality.

A clean `apx-model-store-v1.service` stop removed the listener, unmounted
Btrfs and closed the LUKS mapping. The next start unlocked through TPM2,
remounted the exact filesystem, restarted the cloud-disabled loopback service
and listed the same model. A udev add simulation matched the exact serial and
partition UUID and produced both model-store and Ollama systemd wants. Source
and installed SHA-256 hashes match for both scripts, both units, the udev rule
and Qwen settings. The real cable was not removed because intentional live
hot-unplug would add corruption risk without improving the safe activation
proof.

The new safe-detach controller was also exercised end to end. It returned
`safe-to-remove`, left both services inactive, removed the mount and mapper,
and restored the hidden Host mountpoint as root-owned mode `000`. Reactivation
then TPM-unlocked the same LUKS volume, mounted it read-only, restarted Ollama
and listed the same 18.56 GB model.

## Installed source and rollback

Repository sources:

- `scripts/physical-pilot/apx-model-store-v1.py`;
- `scripts/physical-pilot/apx-local-code-v1.sh`;
- `scripts/physical-pilot/apx-model-store-control-v1.py`;
- `scripts/physical-pilot/apx-model-store-client-v1.py`;
- `config/systemd/apx-model-store-v1.service`;
- `config/systemd/apx-ollama-v1.service`;
- `config/systemd/apx-model-store-control-v1.service`;
- `config/udev/99-apx-model-store-v1.rules`;
- `config/qwen-code/apx-local-coder-v1.json`;
- `tests/test_apx_model_store_physical.py`.

Rollback starts by stopping `apx-model-store-v1.service`, which stops Ollama,
unmounts and closes LUKS. The Host units, udev rule, Qwen defaults, wrapper and
packages can then be removed without touching other APX services. Reformatting
or deleting the model is a separate destructive operation. The old NTFS data
was intentionally destroyed and is not recoverable through this rollback.
