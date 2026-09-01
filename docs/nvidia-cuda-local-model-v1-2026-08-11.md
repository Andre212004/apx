# NVIDIA CUDA local-model path v1 — 2026-08-11

The Host RTX 3060 was previously driven by Nouveau/NVK and Ollama Vulkan.
Measured Qwen2.5-Coder 3B throughput was 30.61 prompt tokens/s and 3.06
generation tokens/s, versus up to 68.47 and 23.36 tokens/s on CPU.

The admitted replacement is `nvidia-open-dkms` 610.43.03 with
`nvidia-utils`, CUDA 13.3 and the Arch `ollama-cuda` backend. DKMS signs all
five NVIDIA modules with the existing APX Secure Boot key via
`/etc/dkms/framework.conf.d/apx-secure-boot-v1.conf`. The normal initramfs
loads `amdgpu`, `nvidia`, `nvidia_modeset`, `nvidia_uvm` and `nvidia_drm`
explicitly and does not contain Nouveau.

The normal signed UKI remains `/EFI/APX/apx-system-v1.efi`. The exact previous
signed UKI was retained as `/EFI/APX/apx-nouveau-recovery-v1.efi`, exposed as
`APX Nouveau Recovery` in systemd-boot. Hold Space during boot to reveal the
menu if recovery is required. Encrypted Host backups are under
`/var/lib/apx/backups/20260811-nvidia-cuda-v1`.

The Fast model selector now resolves to official `qwen2.5-coder:3b`, allowing
Ollama to choose CUDA automatically; the former local alias remains on the SSD
but is no longer selected because it explicitly forced CPU execution.
