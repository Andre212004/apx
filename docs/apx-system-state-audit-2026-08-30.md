# Auditoria do estado APX — 2026-08-30

## Âmbito e resultado

Esta auditoria foi feita depois da recuperação manual do ciclo de boot Windows.
O objetivo foi comparar o sistema físico ativo com o repositório sem copiar
`/etc`, o home do Hub ou `/var/lib/apx` de forma indiscriminada.

O Host está funcional: zero unidades systemd falhadas; Hub oficial, switch de
Environments, host-services v3, power e audio ativos. O finalizador Windows
está inativo com `Result=success`, `ExecMainStatus=0`, `NRestarts=0`. O Linux
Boot Manager é o loader atual e primeiro; não existe `BootNext`.

## Configuração que pertence ao projeto

Os seguintes ativos foram comparados byte a byte entre repositório, seed e
configuração ativa do Hub:

- `hypr/hyprland.lua`, Hypridle e Hyprlock;
- `quickshell/apx/shell.qml` e o calendar store;
- helpers `.local/bin` para shell, consola, terminal, shortcuts, ações do
  portátil e processos detached;
- serviços systemd APX do Host;
- loader systemd-boot, logind, NVIDIA, model-store udev e tmpfiles;
- lifecycle/runner/integração de Environments APX.

Os caminhos ativos acima coincidem com o repositório. O ficheiro legado
`.config/hyprland/hyprland.conf` do Hub difere do seed, mas não é o compositor
ativo: o supervisor seleciona `.config/hypr/hyprland.lua`. Foi preservado como
estado histórico e não sobrepôs a fonte ativa.

Três configurações legítimas estavam apenas no Host e passaram a ter fonte
declarativa própria: `kvmfr` em modules-load/modprobe, a regra udev de
`/dev/kvmfr0` e `apx-pilot-executor.service`. O bootstrap instala agora a
unidade versionada em vez de gerar outra cópia inline.

As entradas `apx-iommu-audit-v1.conf` e `apx-nouveau-recovery-v1.conf` são
wrappers simples para UKIs geridas pelo projeto. A entrada legacy
`apx-headless.conf` contém o UUID LUKS desta máquina e continua a ser gerada
pelo instalador; não foi duplicada como configuração universal. As UKIs e os
backups de header LUKS em `/boot/EFI/APX/recovery` são artefactos binários de
runtime/recuperação, não fontes Git.

## Estado funcional observado

- Hardware: Lenovo 82JU, Ryzen 5 5600H; NVIDIA RTX 3060 Laptop com driver
  `nvidia` 610.43.03 e iGPU Cezanne com `amdgpu`.
- Gráficos: ambos os drivers ativos; framebuffer Looking Glass `kvmfr`
  carregado com 128 MiB e acesso pelo grupo `kvm`/uaccess.
- Rede: Wi-Fi routable/configurado; bridge/veth do Hub routable; Ethernet sem
  carrier. O RTL8852AE está representado nos contratos e payload Windows.
- Bluetooth: integração APX presente, rádio deliberadamente desligado no
  momento da auditoria; não foi gravado como preferência permanente nova.
- Energia: bateria e ações de portátil passam pelo bridge APX; durante a
  auditoria a bateria estava a descarregar. Retomas Windows exigem AC e pelo
  menos 40% antes de qualquer mutação.
- Áudio/volume, brilho, hotkeys, notificações, lock/logout, suspensão,
  reboot/poweroff, input/touchpad/keyboard e displays são implementados pelos
  helpers, QuickShell e serviços versionados acima.
- Locale/timezone: `en_US.UTF-8`, teclado `pt-latin1`/layout `pt`, timezone
  `Europe/Lisbon`, NTP sincronizado e RTC em UTC.
- Armazenamento APX: `/var/lib/apx` permanece o estado persistente dos
  Environments; nenhum environment, release ou dado de utilizador foi copiado,
  movido ou removido nesta auditoria.

## O que permanece fora de Git

Estado runtime e regenerável:

- pending/status/logs/locks, metadata transacional, failures e backups;
- WIM/SWM/ISO, UKIs assinadas, BCD binário, firmware variables e caches;
- `__pycache__`, `.pyc`, crash dumps, logs, browser component updates e
  temporary files;
- cópias `.before-*` e `.apx-backup-*` instaladas.

Dados pessoais ou credenciais que nunca entram no repositório:

- perfis Brave, cookies, Login Data, History, IndexedDB, Local Storage,
  WhatsApp/webmail state, wallet state e certificados locais;
- passwords, tokens, private keys, Secure Boot private material, machine
  credentials e histories;
- homes, documentos e conteúdo dos Environments.

Identidades físicas como GUID GPT, PARTUUID e serial aparecem apenas nos
contratos de segurança específicos deste pilot, porque são verificadores do
alvo e não segredos. Nenhuma password ou chave foi copiada para os contratos.

## Validação

A suite completa passou 1102 testes com 11 skips esperados. Todos os Python
alterados compilam; todos os shell alterados passam `bash -n`; as unidades
systemd do Host passam `systemd-analyze verify`; `git diff --check` está limpo.
As unidades initrd foram validadas pelos testes/fixtures próprios, porque os
executáveis referidos só existem dentro da imagem initramfs e, corretamente,
não no rootfs do Host.
