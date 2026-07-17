# APX Local Development Agent v1

Status: accepted installation addition for the owner-controlled physical
development pilot. The first instance is Development-local and CPU-first. It
is not a host service, Hub capability, production APX component, or accepted
cross-Environment assistant design.

## Purpose

The physical Development Environment should retain a useful offline coding
fallback when Codex is unavailable or its remote allowance is temporarily
exhausted. The fallback may review files, explain errors, propose tests, improve
documentation, and perform small, reviewable source changes. Codex remains the
primary implementation and review tool while it is available.

The fallback does not approve its own output, promote releases, administer the
host, control the Hub, or weaken the normal Development-to-Hub admission
boundary. Local inference removes a cloud dependency; it does not make generated
code trusted.

## Initial Selection

The initial pilot selection is:

- model: `Qwen2.5-Coder 7B Instruct`;
- pilot representation: Ollama `qwen2.5-coder:7b`, currently a roughly 4.7 GB
  quantized model with a 32K served context;
- model licence: Apache-2.0 according to the upstream model card;
- local model server: the official Arch `ollama` package, CPU-first;
- terminal coding agent: the official Arch `qwen-code` package;
- endpoint: Environment loopback only, `127.0.0.1:11434`;
- owner: the Development Environment and its local service/user state.

This selection fits the known 6 GB RTX 3060 Mobile substantially better than
current 30B-class coder models. It is still conditional on the physical
preflight measuring sufficient system memory and disk space. If the 7B model
cannot run reliably with the measured memory ceiling, the admitted fallback is
`qwen2.5-coder:3b`; silently substituting a larger model is not allowed.

The owner has deferred this installation until an external SSD is available
and may later prefer a larger model. Extra capacity does not approve that model
or its storage path. `external-development-model-storage-v1.md` defines the
identity, encryption, visibility, integrity, disconnect, and recovery gates
that must pass before external model storage is implemented.

The first run is deliberately CPU-first. The headless APX pilot has not admitted
NVIDIA devices, host driver interfaces, or CUDA userspace into Development.
Installing `ollama-cuda` before that boundary has been designed and tested would
turn an assistant convenience into an undocumented device-isolation exception.

The physical headless pilot now assigns quotas by role. Hub and Minimal retain
small 4 GiB root and 2 GiB home limits. Development receives a bounded 16 GiB
root and 8 GiB home. The model and Ollama package/service state live in the
Development root; Codex state, credentials, repository, and user tooling live
in its home. These limits allow the roughly 4.7 GB model plus packages,
downloads, caches, and working space without turning the approximately 471 GiB
of currently free host capacity into an unbounded Environment allocation.
They are experimental pilot limits, not production defaults.

## Environment Boundary

The initial instance belongs only to Development:

- executable, dependencies, service configuration, model files, prompts,
  indexes, caches, and mutable state stay in Development;
- the server listens only on Environment loopback and is not published on the
  host, Hub, another Environment, or the physical network;
- the service starts and stops with Development;
- stopping Development must leave no assistant process or listening socket;
- destroying Development destroys its assistant state under the normal
  Environment lifecycle;
- the Hub contains neither Ollama, Qwen Code, model weights, assistant history,
  nor a proxy to the Development instance.

Other Environments may later opt into their own local instance through a
reviewed role or explicit policy. V1 does not share a running server, writable
model directory, conversation memory, repository index, or tool authority
between Environments. A future verified, immutable, read-only model artifact may
reduce disk duplication, but that storage design is still open.

High Security Environments exclude assistants by default. A general-purpose
assistant must not be granted APX executor access merely so it can help with an
installation. It may operate through that Environment's approved local package
and file permissions only.

## Operating Policy

Qwen Code begins in its confirmation-based mode. The owner reviews diffs and
command requests before they run. The local agent may:

- read files explicitly placed in its current Environment;
- review source and documentation;
- explain compiler, test, package-manager, and service errors from supplied
  output;
- propose or make small changes inside the current Development checkout;
- run bounded repository tests after approval;
- prepare commits, but never commit or push unless the owner explicitly asks.

It may not:

- use an automatic or unrestricted approval mode;
- access the host filesystem, Hub state, executor socket, another Environment,
  credentials, or unrelated personal files;
- run host package management or APX lifecycle operations;
- promote, admit, sign, install, or approve an APX release;
- continue a destructive installation from incomplete or ambiguous evidence;
- claim that its review replaces tests, Codex review, or the APX promotion
  boundary.

For installation troubleshooting, the preferred interaction is to paste
sanitized command output into the agent. Secrets, recovery passphrases, tokens,
SSH private keys, and authentication state are never supplied.

## Physical-Pilot Admission Checks

After Codex works inside Development and before enabling the local service, the
pilot records:

- total and available system memory;
- free Environment storage;
- package names and installed versions;
- exact selected Ollama model identity and observed model size;
- that the Ollama listener is only `127.0.0.1:11434` inside Development;
- that the host and Hub cannot reach that endpoint;
- that Qwen Code can perform a read-only repository review;
- that command/file changes still require confirmation;
- that stopping Development removes the process and listener;
- that restarting Development preserves only its own declared model and agent
  state.

The 7B model is admitted only if it answers reliably without memory pressure
that destabilizes Development or the host. Model speed is measured rather than
promised. The CPU-first fallback may be slow on repository-scale prompts; its
role is continuity for bounded work, not parity with Codex.

## Later GPU and Multi-Environment Work

CUDA acceleration requires the normal APX GPU gates: exact host driver and
userspace compatibility, explicit device policy, cgroup resource limits,
teardown proof, denial tests from other Environments, and evidence that no
assistant process survives Environment stop. Only then may a reviewed
Development role use `ollama-cuda` or another GPU runtime.

Provisioning the assistant in multiple Environments additionally requires a
typed opt-in policy, per-Environment storage/accounting, CPU/memory/GPU limits,
network policy, update/provenance rules, and tests proving that files, prompts,
indexes, and mutable memory do not cross boundaries.

## Removal

The assistant is optional. Removing Qwen Code, Ollama, and the model from
Development must not alter Codex, the Hub, host, base, executor, or another
Environment. Recreating Development from an assistant-free release is the
cleanest later removal path.

## Upstream References

- Qwen2.5-Coder 7B Instruct model card and Apache-2.0 licence:
  `https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct`;
- Ollama model representation and served sizes:
  `https://ollama.com/library/qwen2.5-coder`;
- Qwen Code local-provider support:
  `https://github.com/QwenLM/qwen-code`;
- official Arch packages:
  `https://archlinux.org/packages/extra/x86_64/ollama/` and
  `https://archlinux.org/packages/extra/x86_64/qwen-code/`.
