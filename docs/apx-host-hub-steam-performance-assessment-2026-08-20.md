# Avaliação de performance APX: Host, HUB e Steam

Data: 20 de agosto de 2026
Hardware: Lenovo Legion, Ryzen 5 5600H (6C/12T), 27,3 GiB RAM, Samsung PM981 NVMe, Radeon Cezanne + RTX 3060 Laptop 6 GiB, Realtek RTL8852AE Wi‑Fi 6
Comparador: Host nativo do mesmo computador, não outro equipamento

## Conclusão executiva e estado corrigido

O isolamento por `systemd-nspawn` não introduz uma penalização relevante em CPU single-thread, chamadas ao sistema, memória ou latência básica. A experiência de rede também não mostra uma perda de throughput atribuível ao APX; nesta janela, HUB e Steam chegaram até a medir mais do que o Host, o que confirma que a variabilidade do Wi‑Fi/WAN domina o resultado.

O ensaio inicial encontrou dois bloqueios graves para considerar o perfil Gaming equivalente a um computador normal:

1. A carga CPU com 12 threads ficava aproximadamente **49% abaixo do Host nativo**.
2. O Steam cria uma instância Vulkan, mas enumera **apenas a Radeon integrada**. A RTX 3060 não aparece. `/dev/nvidia-uvm` e `nvidia-uvm-tools` não são entregues ao Environment e faltam as bibliotecas gráficas `lib32-*` necessárias a muitos jogos Steam/Proton.

Estes bloqueios foram corrigidos e fisicamente revalidados no mesmo dia. A causa CPU era a quota externa `CPUQuota=600%`, que limitava cada Environment a seis CPUs apesar de os cgroups descendentes mostrarem `cpu.max=max`. A quota é agora `1200%` e o cgroup físico mostrou `1200000 100000`. A validação pós-correção mediu 15,06 GB/s numa passagem Steam autenticada e 20,62 GB/s numa passagem administrativa curta, eliminando o teto anterior de ~7,2–7,6 GB/s.

A RTX 3060 é agora enumerada por NVML e Vulkan dentro do Steam. O launcher cria e admite os dois nós UVM, e expõe somente `/sys/module/nvidia` em modo read-only: com `--private-network`, o nspawn ocultava `nvidia/initstate`, levando o userspace a declarar falsamente que o driver estava bloqueado. O Steam tem agora a pilha Vulkan 64/32-bit coerente, incluindo `lib32-nvidia-utils 610.43.03-1`, correspondente ao driver Host 610.43.03.

A validação final de 21 de agosto, já ligada à corrente, não encontrou overhead mensurável no disco nem na RTX. I/O direto de 256 MiB deu médias de ~638 MB/s Host contra ~655 MB/s HUB em escrita e ~3,07 contra ~2,97 GB/s em leitura. No mesmo Hyprland, socket Wayland, rootfs, binário, ICD, RTX e resolução, `vkmark` comparou o processo APX normal com um processo Host fora do user namespace/cgroup APX. O aquecimento marcou 691 em ambos; três pares a 3840×2160 marcaram APX 93/192/192 e Host 92/191/192, médias 159,0 e 158,3. A diferença de ~0,4% favorece nominalmente o APX e é apenas ruído de medição. A fase de performance estrutural fica encerrada sem bloqueio conhecido; performance específica de um jogo continua dependente do próprio título.

## Remediação física aplicada

- quota CPU do launcher: `600%` → `1200%`;
- NVIDIA: criação/validação de `/dev/nvidia-uvm` e `/dev/nvidia-uvm-tools`, com majors dinâmicos comprovados em `/proc/devices`;
- sysfs NVIDIA: bind read-only mínimo de `/sys/module/nvidia`, mantendo rede privada e `DevicePolicy=closed`;
- Steam/Proton: multilib ativado e `lib32-mesa`, `lib32-vulkan-radeon`, `lib32-vulkan-icd-loader`, `lib32-nvidia-utils`, `egl-gbm` e `vulkan-tools` instalados;
- imagem futura: runtime e construtor físico passam a ativar multilib e instalar a mesma base gráfica;
- input: Hyprland final enumerou os dois teclados internos, rato ELAN e touchpad ELAN. As mensagens seatd remanescentes são recusas esperadas durante descoberta de dispositivos fora da allowlist, não perda dos dispositivos admitidos.
- armazenamento: `fstrim.timer` semanal ativado; CoW, compressão, checksums, snapshots e qgroups foram preservados porque o teste AC não justificou enfraquecer essas garantias.

O sistema Steam ficou coerente (`pacman -Dk` sem erros), os QML temporários foram restaurados byte a byte e o HUB voltou a ser o único Environment ativo. A suíte completa passou 1043 testes, com 11 skips esperados.

## Condições e método

- Testes executados no Host, no HUB ativo e no Environment `steam` da geração `72f90ce8`.
- Máquina em bateria, a descarregar, governador `powersave` e preferência energética `balance_performance`. Os valores absolutos não representam o máximo ligado à corrente.
- Duas passagens por contexto para SHA-256 single-thread, cópia de memória, `stat`, criação de processos, jitter de `sleep(1 ms)`, escrita/leitura de 256 MiB e `fsync` de 4 KiB.
- Validação multi-core intercalada Host → HUB → Host com 12 workers e blocos SHA-256 de 16 KiB.
- Rede medida contra Cloudflare e por ping no Host. O Wi‑Fi físico pertence ao Host; os Environments usam rede privada com NAT.
- Vulkan validado no Steam diretamente contra `libvulkan.so.1`, sem depender de `vulkaninfo`.
- As transições foram feitas pelo caminho autenticado da QuickShell. No fim, apenas `apx-hub` ficou ativo e os QML de HUB e Steam foram restaurados byte a byte.
- A validação final de 21 de agosto foi feita com `ADP0=1`. O teste Vulkan usou `vkmark 2025.01`, seis cenas a 3840×2160 e apresentação imediata. O processo Host entrou somente no mount namespace do HUB para alcançar o mesmo socket Wayland; permaneceu fora do user namespace e do cgroup APX.

## Resultados

| Área | Host nativo | HUB | Steam | Leitura |
|---|---:|---:|---:|---|
| CPU SHA-256, 1 thread | 1288 MiB/s | 1293 MiB/s | 1295 MiB/s | Diferença inferior a 1%; sem overhead mensurável |
| CPU SHA-256, 12 threads, 16 KiB | 14,62–14,93 GB/s | 7,64 GB/s | 7,15 GB/s numa passagem longa | Défice multi-core de cerca de 49% |
| Cópia de memória | 12,3–13,0 GiB/s | 13,6–14,5 GiB/s | 7,5–16,2 GiB/s | Muito variável; sem evidência de limite de RAM |
| Chamadas `stat` | 260–317 mil/s | 293–299 mil/s | 303–304 mil/s | Mesma classe de performance |
| Criação de processos | 1329–1963/s | 1262–1307/s | 1240–1260/s | Pequena penalização provável; Host teve grande variação |
| Excesso mediano sobre `sleep(1 ms)` | 0,082 ms | 0,090 ms | 0,118 ms | Acréscimo Steam de apenas ~0,036 ms |
| Escrita 256 MiB + `fsync` | 618–862 MiB/s | 615–642 MiB/s | 595–602 MiB/s | Steam ~19% abaixo da média Host; armazenamento Btrfs variável |
| Leitura 256 MiB | 1523–1871 MiB/s | 1601–1643 MiB/s | 1204–1370 MiB/s | Steam abaixo nesta janela; cache influencia muito |
| `fsync` 4 KiB, p50 | 3,27–3,33 ms | 3,28–3,30 ms | 3,66–3,68 ms | Steam ~0,38 ms acima |
| Download WAN de 25 MB | 34,9 Mbit/s | 47,3 Mbit/s | 55,1 Mbit/s | Não há evidência de penalização NAT; Wi‑Fi/WAN dominam |
| TTFB Cloudflare, mediana | 60,8 ms | 237,8 ms | 83,6 ms | HUB teve uma passagem anómala; não generalizar |
| Consulta PipeWire ao volume, p50 | — | 10,66 ms | 10,66 ms | Praticamente idêntico |
| Estado Wi‑Fi via serviço Host, p50 | — | 78,49 ms | 78,26 ms | Mediação estável entre Environments |
| Estado Bluetooth via serviço Host, p50 | — | 101,67 ms | 96,74 ms | Mediação estável entre Environments |
| Snapshot completo Host, p50 | — | 116,13 ms | 116,50 ms | Mesmo custo |
| Entrada no Steam | — | pedido | pronto em 10,35 s | Passagens observadas: ~10–17 s |
| Regresso ao HUB | — | pronto em 8,55 s | pedido | Outras passagens: ~10 s |

### Validação final ligada à corrente — 21 de agosto

| Prova | Host | APX/HUB | Diferença observada |
|---|---:|---:|---:|
| Escrita direta incompressível, 256 MiB, média de 3 | ~638 MB/s | ~655 MB/s | APX +2,7%; variação normal |
| Leitura direta, 256 MiB, média de 3 | ~3,07 GB/s | ~2,97 GB/s | APX -3,3%; variação normal |
| `vkmark` 1080p, aquecimento completo | 691 | 691 | 0,0% |
| `vkmark` 4K, par frio | 92 | 93 | APX +1 ponto |
| `vkmark` 4K, dois pares estabilizados | 191 / 192 | 192 / 192 | 0–1 ponto |
| `vkmark` 4K, média dos três pares | 158,3 | 159,0 | APX +0,4%; sem overhead mensurável |

O salto do primeiro par 4K para os pares seguintes ocorreu simultaneamente nos dois contextos e representa o ramp de power-state/boost da RTX, não isolamento. Nos pares estabilizados, cada cena APX/Host ficou igual ou separada por apenas 1 FPS, com frametimes de 5,10–5,59 ms.

### CPU e escalonamento

O resultado single-thread elimina a hipótese de uma penalização intrínseca grande do contentor. O défice aparece quando os 12 workers competem em simultâneo. A validação curta intercalada deu 14,62 e 14,93 GB/s no Host, com 7,64 GB/s no HUB entre ambos, por isso não é explicado apenas por aquecimento ou ordem do teste.

O diagnóstico inicial falhou ao observar apenas os cgroups descendentes no namespace. A unidade externa transitória tinha `CPUQuotaPerSecUSec=6s`, isto é, `cpu.max = 600000 100000`. Assim, eram visíveis 12 CPUs, mas só havia orçamento equivalente a seis CPUs por período. Depois da correção:

- afinidade efetiva `0-11`;
- unidade externa com `CPUQuotaPerSecUSec=12s`;
- `cpu.max = 1200000 100000`;
- `Nice=0`, política normal;
- unidade do HUB com `CPUWeight=200`.

O teto de ~7,6 GB/s desapareceu: o Steam pós-correção atingiu 15,06 GB/s numa passagem completa e 20,62 GB/s numa passagem curta. A variação absoluta continua dependente de frequência, bateria e temperatura, mas já não existe a perda estrutural de ~49%.

### GPU e Gaming

No Host, Vulkan enumera a Radeon integrada e a RTX 3060. No Steam, o probe Vulkan devolveu sucesso (`vkCreateInstance=0`) mas apenas um dispositivo:

```text
AMD Radeon Graphics (RADV RENOIR), vendor 0x1002, device 0x1638
```

O Environment recebe `/dev/dri/card0`, `card1`, `renderD128`, `renderD129` e `/dev/nvidia{0,ctl,-modeset}`, mas não recebe `/dev/nvidia-uvm` nem `/dev/nvidia-uvm-tools`. Tem `nvidia-utils 610.43.03`, `mesa`, `vulkan-radeon` e `vulkan-icd-loader`, mas não tem `vulkan-tools` nem os equivalentes `lib32-mesa`, `lib32-vulkan-radeon`, `lib32-vulkan-icd-loader` e `lib32-nvidia-utils`.

No estado corrigido, `nvidia-smi` dentro do Steam devolve `NVIDIA GeForce RTX 3060 Laptop GPU, 610.43.03, 6144 MiB`, e `vulkaninfo` forçado ao ICD NVIDIA enumera a mesma GPU com `driverName=NVIDIA`. A pilha 32-bit está instalada. O `vkmark` ligado à corrente prova paridade do caminho Vulkan/RTX; não existem jogos nem manifests instalados no Steam, pelo que não há ainda um resultado específico de um título.

Os logs seatd continuam a mostrar `Operation not permitted` quando libinput tenta descobrir hardware que a política APX não arrendou. Não se abriu a allowlist para silenciar logs. A prova final de `hyprctl devices` enumerou os quatro caminhos de input pretendidos, pelo que estas recusas são o efeito esperado da fronteira fechada, não uma falha funcional de teclado/rato/touchpad.

### Wi‑Fi e rede

O RTL8852AE estava ligado à rede `Casa`, com cerca de -54 dBm no Host. O ping ao router teve média de 16,85 ms, pico de 91,57 ms e 0% de perda. Para 1.1.1.1, a média foi 32,67 ms, pico 126,34 ms e 10% de perda. Estes picos explicam a grande dispersão de TTFB.

O ping não funciona como utilizador normal nos Environments porque `CAP_NET_RAW` não é concedida. Uma ligação TCP do HUB para o gateway do Host também é bloqueada. São propriedades de isolamento, não provas de rede lenta. O download HTTP mostrou que o NAT do Environment não é o estrangulamento principal.

### Bluetooth e áudio

O controlador BlueZ estava presente e ligado; `discovering=false`, `pairable=false` e não existiam dispositivos emparelhados. A consulta mediada custa cerca de 97–102 ms. Sem um periférico real emparelhado não foi possível certificar throughput, latência de áudio Bluetooth, estabilidade HID ou handoff entre Environments. Esses resultados não devem ser anunciados como aprovados.

O caminho áudio local responde em cerca de 10,7 ms tanto no HUB como no Steam. Isto mede consulta/controlo PipeWire, não latência acústica round-trip, que exige interface de loopback ou microfone de medição.

## Prioridades recomendadas

1. **Aceitação por título:** quando existir um jogo instalado, recolher FPS médio, 1% low e frametime p95/p99; isto valida o jogo/Proton, não um bloqueio APX atualmente conhecido.
2. **Hardware opcional:** ligar um comando, um dispositivo Bluetooth e um servidor LAN `iperf3` quando estiverem fisicamente disponíveis.

## Estado final e limites

Depois da avaliação inicial foram instaladas as dependências gráficas 32-bit no Steam e alteradas as políticas de CPU e admissão NVIDIA descritas acima. A fronteira de dispositivos continua fechada e a rede continua privada. A repetição ligada à corrente mede disco dentro de ~3% e Vulkan dentro de ~0,4% do processo Host equivalente; não há penalização estrutural relevante face a Arch+Hyprland no mesmo hardware e stack. `vkmark` e `assimp` foram removidos depois da prova. O HUB voltou a ser o único Environment ativo, no ecrã de login normal; nenhuma credencial foi automatizada. Um jogo real continua necessário apenas para caracterizar esse título, Proton e os seus 1% lows.
