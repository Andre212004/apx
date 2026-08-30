# Windows nativo repetível — estado de 2026-08-25

> **Documento histórico.** O estado operacional descrito abaixo foi
> ultrapassado pelo incidente de 2026-08-26/30. Em particular, já não existe
> retoma automática baseada apenas em `windows-pending.json`. A máquina de
> estados fail-closed e o runbook atual estão documentados em
> `native-windows-fail-closed-v2-2026-08-30.md`.

## Resultado atual

O Environment `Windows` deixou de usar QEMU. É um Windows 11 instalado numa
partição física do NVMe e aparece no HUB com a identificação especial
`NATIVO`. O arranque usa a entrada UEFI própria do Windows apenas uma vez; a
ordem de arranque permanente continua a colocar o APX/Linux em primeiro lugar.

O runner valida antes de cada transição a identidade e o tamanho do disco, as
PARTUUIDs, o GPT, o Windows Boot Manager assinado, o BCD dentro de limites e a
ausência de um `BootNext` inesperado. Depois arma apenas a entrada Windows com
`efibootmgr -n`. Se a preparação falhar, limpa `BootNext`.

O Windows atualmente instalado está pronto e funcional. A atualização normal
do Windows pode mudar os bytes do Boot Manager; por isso a admissão verifica a
assinatura Secure Boot da Microsoft e a identidade física, e não depende de um
hash imutável de um ficheiro que o próprio Windows atualiza.

## Regresso ao HUB

Foi colocado no Windows um helper que regista `SUPER+E`/`Win+E` com as APIs
nativas do sistema e reinicia o computador. Como o APX está primeiro na ordem
UEFI, o reinício regressa ao HUB. Não há agente externo, AutoHotkey nem
PowerToys. O helper é iniciado de forma invisível e supervisionada pelo Common
Startup; o antigo atalho público `REGRESSAR AO APX.cmd` foi removido.

No primeiro início de sessão, o Explorer pode ainda capturar `Win+E` antes de
reler a política. Nesse caso funciona `Win+Shift+E`; após terminar e voltar a
iniciar sessão, `Win+E` fica reservado ao helper APX.

## Criação pelo menu de Environments

O formulário do HUB permite escolher `Windows nativo` e um dos tamanhos
admitidos: 80, 120 ou 160 GiB; 120 GiB é o valor predefinido. Só é permitida uma
instância física. A política preserva no mínimo 256 GiB para APX e exige margem
operacional adicional antes de aceitar a redução.

A criação não redimensiona um sistema montado de forma improvisada. O Host
constrói uma UKI assinada com uma ação única e identidades exatas. No arranque
offline, a UKI:

1. valida disco, geração, tamanhos e estado esperado;
2. reduz primeiro o Btrfs APX;
3. fecha o volume dm-crypt;
4. reduz a partição Linux;
5. cria MSR, Windows, Recovery e o ESP interno de instalação;
6. prepara o instalador e deixa o firmware regressar ao APX por omissão.

O instalador interno inclui o controlador Lenovo/Realtek RTL8852AE e o helper
de regresso ao HUB. Não requer uma pen USB.

## Eliminação e recuperação do espaço

Eliminar `Windows · NATIVO` exige a confirmação forte do menu. A ação offline
recusa continuar se a disposição não corresponder exatamente às quatro
partições esperadas. Só então descarta os intervalos físicos Windows, elimina
as partições 3–6 e aumenta a partição APX. No arranque seguinte, o finalizador
expande dm-crypt e Btrfs para devolver efetivamente o espaço ao sistema.

O processo não permite nomes arbitrários, mais de uma instância, tamanhos fora
da lista ou discos/partições com identidades diferentes das aprovadas.

## Validação e limite conhecido

- O arranque da instalação e do Windows atual foi exercitado no hardware real.
- O runner instalado passa `--validate-only`; Linux permanece primeiro e não
  existe atualmente `BootNext` armado.
- O helper de regresso foi escrito e verificado byte a byte na partição Windows.
- A criação/eliminação passa os testes de contrato, segurança e uma simulação
  GPT descartável. A suite completa passa 1087 testes, com 11 omissões esperadas.
- A primeira criação ou eliminação destrutiva pelo novo fluxo ainda não foi
  executada no NVMe real, porque isso apagaria o Windows funcional acabado de
  instalar. Esta é a única prova de aceitação física ainda pendente.

As cópias físicas relevantes estão em
`/var/lib/apx/backups/20260825-native-windows-ready-v2`,
`/var/lib/apx/backups/20260825-native-windows-return-v1` e
`/var/lib/apx/backups/20260825-native-windows-lifecycle-v1`.

## Base de controladores e regresso

Cada novo instalador Windows nativo inclui o controlador oficial Lenovo
RTL8852AE deste computador `82JU`, tanto no WinPE como na imagem instalada. O
Windows Setup executa `pnputil` como `SYSTEM`; o APX não publica a geração como
pronta enquanto o DriverStore não contiver um INF para
`PCI\VEN_10EC&DEV_8852&SUBSYS_485217AA`.

O mesmo instalador coloca no Common Startup um helper invisível e
supervisionado. `SUPER+E` faz um reinício normal do Windows e a ordem UEFI, com
Linux primeiro, regressa ao HUB. `SUPER+SHIFT+E` fica disponível no primeiro
início de sessão enquanto o Explorer relê a reserva de `WIN+E`. Não é colocado
qualquer ícone APX no Ambiente de Trabalho público. Os validadores de conclusão
e arranque exigem o helper e a ausência do ícone antigo.

Os controladores incluídos no Windows cobrem a instalação e o armazenamento.
Depois de o Wi-Fi garantido estar ativo, o Windows Update obtém as revisões
assinadas atuais de AMD/NVIDIA, áudio, Bluetooth, câmara e Lenovo para o mesmo
hardware. O APX não copia aplicações, perfis de utilizador ou ficheiros pessoais
entre gerações Windows.

## Primeira tentativa física de eliminação

A primeira confirmação real de eliminação terminou em recusa segura antes do
reinício. O executor transitório herdava `/`, mas o construtor da UKI assinada
exige que o diretório de trabalho seja a raiz exata e validada do repositório.
Por isso devolveu `repository differs`. Não foi armado `BootNext`, não ficou
operação pendente e nenhuma partição foi alterada ou eliminada.

O executor passa agora explicitamente a raiz validada ao criar subprocessos.
O preflight instalado aceita a geração Windows atual de 120 GiB, os artefactos
temporários continuam ausentes e os 1089 testes passam, com 11 omissões
esperadas. A prova destrutiva no NVMe continua pendente até o proprietário
repetir a eliminação no HUB. Rollback da correção:
`/var/lib/apx/backups/20260825T222335Z-native-windows-lifecycle-cwd-fix-v1`.

## Recusa física no tipo GPT

A tentativa seguinte arrancou corretamente a UKI assinada, mas recusou em
`msr-type` antes do primeiro descarte. O `blkid` 2.42.2 deste Host não devolve
`PART_ENTRY_TYPE` pela consulta normal ao dispositivo; essa informação exige a
sondagem direta `-p`. As quatro partições Windows continuaram presentes e todos
os seus tipos, inícios, tamanhos, sistemas de ficheiros e identificadores eram
os esperados.

As quatro verificações GPT usam agora `blkid -p`. Após validar que não existia
qualquer alteração física, o APX arquivou e removeu apenas os artefactos da
tentativa falhada. Uma nova UKI foi construída, verificada, extraída e o script
incorporado confirmou as quatro sondagens corrigidas. A imagem de teste foi
removida sem armar `BootNext`; os 1089 testes passam com 11 omissões esperadas.
O Windows permanece intacto até nova confirmação de eliminação pelo
proprietário. Cópia da recusa:
`/var/lib/apx/backups/20260826T143302Z-native-windows-msr-probe-refusal-v1`.

## Eliminação física concluída

A repetição corrigida concluiu a fase offline: descartou e eliminou apenas p3 a
p6 e aumentou p2 para 511035383296 bytes. No arranque Linux seguinte, o volume
cifrado foi automaticamente reaberto com 511018606080 bytes. O finalizador
deixou de repetir `cryptsetup resize`, porque essa chamada redundante tentava
ler autenticação num serviço sem teclado; agora exige o tamanho completo como
pré-condição.

O Btrfs foi aumentado com `1:max` para 511018602496 bytes. Os 3584 bytes
restantes são apenas alinhamento ao bloco de 4096 bytes. Foram removidos os
metadados Windows, marcador pendente, estado offline, UKI/entrada de manutenção
e as entradas UEFI Windows/APX Setup. O disco contém apenas APX EFI e APX CRYPT,
o catálogo já não publica Windows e aproximadamente 450096533504 bytes estão
disponíveis. A eliminação e devolução física de espaço ficam aceites no NVMe
real; falta ainda aceitar a recriação completa de um Windows novo. Backup:
`/var/lib/apx/backups/20260826T144156Z-native-windows-delete-finalize-v1`.

## Ciclo autónomo e retomável

O ciclo instalado deixou de usar ficheiros executáveis da pasta de
desenvolvimento. Os ativos revistos ficam em
`/usr/share/apx/native-windows-lifecycle-v1` e os executores fixos em
`/usr/lib/apx`. Assim, criar ou apagar não depende de uma sessão Codex, do
diretório atual nem de executar a suite de testes no momento da operação.

As fases são persistentes e idempotentes. A eliminação grava `finalizing` antes
da limpeza e só remove o marcador pendente no fim. A criação usa
`preparing-installer` e `installing`; um marcador exato permite repetir a
preparação do instalador e o APX retoma automaticamente APX Setup ou Windows
Boot Manager durante até oito reinícios. Falhas transitórias do finalizador são
repetidas três vezes, mantendo sempre limites e identidades físicas.

Como prova não destrutiva, o construtor instalado foi executado a partir de `/`,
criou uma UKI `create/120 GiB` assinada e a imagem foi extraída: executor e
serviço incorporados coincidiram byte a byte com os ativos instalados. A imagem
foi removida sem `BootNext`, operação pendente ou alteração GPT. Os 1089 testes
passam com 11 omissões esperadas. Rollback:
`/var/lib/apx/backups/20260826T145246Z-self-contained-native-windows-lifecycle-v1`.

## Contrato WinPE explícito v2

A recriação seguinte demonstrou uma falha importante no fluxo antigo: o WinPE
arrancava e os `install*.swm` eram válidos, mas o processo assumia números de
partição históricos e não concluía nem validava toda a cadeia DISM → BCDBoot →
BCD → UEFI. Ficou uma instalação OOBE incompleta e `APXWINSETUP` sem um registo
Windows publicável no HUB.

O fluxo corrigido cria apenas duas partições no espaço reservado: p3 NTFS
`APXWINTARGET`, com o tamanho escolhido, e p4 FAT32 `APXWINSETUP`, com 9 GiB.
A p1 `APX_EFI` existente continua a ser a única ESP. Um contrato imutável é
colocado no WinPE, na partição alvo, no suporte de instalação e na ESP. O WinPE
localiza o disco pelo GUID GPT e cada partição pelo conjunto tipo GPT,
PARTUUID, label e tamanho; as letras `W:`, `C:` e `S:` são temporárias e só são
atribuídas depois desta autenticação.

Antes de alterar p3, o script confirma os três SWM e que o índice 6 é Windows
11 Pro. Só então formata a partição alvo autenticada e executa a aplicação
dividida com `/ImageFile:W:\sources\install.swm` e
`/SWMFile:W:\sources\install*.swm`. Depois instala offline os ativos de Wi-Fi
e regresso ao HUB, executa `bcdboot C:\Windows /s S: /f UEFI /v` sobre a p1
autenticada e valida `EFI\Microsoft\Boot\bootmgfw.efi`, o BCD, `device`,
`osdevice` e `\Windows\system32\winload.efi`. Uma falha em qualquer porta grava
o erro e regressa ao Linux sem tentar formatar outra partição.

`APXWINSETUP` e os contratos de recuperação ficam presentes durante OOBE e
reinícios do Windows. Só depois de existir um perfil real e de serem validados
o helper invisível de `SUPER+E` e o controlador Wi-Fi é que o Windows aparece
como `ready` e o suporte pode ser recuperado.

## Arranque de manutenção sem menu técnico

Criar/apagar deixou de selecionar a UKI através do systemd-boot. O runner cria
uma entrada UEFI temporária diretamente com `efibootmgr --create-only`, confirma
que a `BootOrder` Linux-first não mudou, apaga o ficheiro que a faria aparecer
no menu e arma essa entrada apenas em `BootNext`. No regresso, o finalizador
remove a entrada UEFI e a UKI. Assim o utilizador não volta a ficar no ecrã com
“Windows” e várias opções APX durante uma operação automática.

A instalação incompleta foi eliminada após validação exata e todo o espaço foi
devolvido ao APX. Atualmente só existem p1 e p2, não há Windows oculto nem
operação pendente, e nenhuma nova instalação/reinício está armada. Os 1089
testes passam com 11 omissões esperadas. Rollback da versão instalada:
`/var/lib/apx/backups/20260826T161719Z-native-windows-explicit-winpe-v2`.

## Falha `findstr` e recuperação v3 preparada

A recriação física de 160 GiB confirmou que o `boot.wim` usado não inclui
`findstr.exe`. O comando antigo dependia dele logo na pesquisa do disco, pelo
que o WinPE regressou ao APX antes de formatar p3. A partição alvo continua a
conter apenas o contrato APX; os três SWM, p1/p2, a ordem UEFI e o suporte p4
estão intactos. Não existe ainda Windows aplicado, BCD ou Windows Boot Manager.

O comando revisto usa apenas parsing interno de `cmd.exe`. Localiza o disco
pelo GUID/tamanho GPT e cada papel pelo tipo GPT, label e tamanho esperado;
as letras temporárias são escolhidas entre letras realmente livres. Os
contratos idênticos em WinPE, p3, p4 e p1 continuam a ligar essa observação à
geometria/PARTUUID exata criada e validada pelo Host. Antes da única formatação
NTFS, o script repete a identificação do disco e de p3 e volta a comparar o
contrato. Qualquer divergência termina sem tocar noutra partição.

Após DISM com `/SWMFile:...install*.swm`, as barreiras exigem o loader e hive
offline, os ativos APX, BCDBoot na ESP APX autenticada, `bootmgfw.efi`, BCD,
`device`, `osdevice`, `winload.efi` e entrada de firmware, além de confirmar
que systemd-boot e `APXWINSETUP` continuam presentes. O finalizador também
passa a tratar a ausência de `Users` como instalação incompleta retomável, e o
menu permanece ocupado enquanto existir o marcador pendente, mesmo quando a
mensagem visível é de falha.

Uma recuperação física em duas autorizações está preparada no repositório. A
primeira fase substitui atomicamente apenas o `boot.wim` autenticado de p4 e
instala os executores corrigidos, sem reiniciar nem armar UEFI. A segunda fase,
explicitamente pedida com `--reboot`, repete toda a validação e só então retoma
APX Setup. Nenhuma destas fases foi ainda executada no Host.

A suite completa do repositório passa 1090 testes com 11 omissões esperadas.
Um ensaio sobre uma cópia temporária do `boot.wim` atual reconstruiu e
verificou integralmente a imagem e extraiu o novo comando e o contrato com
bytes exatos. A cópia temporária foi removida; p4 não foi escrita.

## Recuperação exclusivamente pelo menu Environments

O fluxo suportado para o utilizador deixa de incluir adaptadores ou comandos
manuais. Uma criação Windows que termine em falha continua a bloquear operações
sobrepostas, mas aparece no menu com duas escolhas autenticadas:

- `RETOMAR WINDOWS` recomeça somente a instalação Windows incompleta;
- `APAGAR INCOMPLETO` exige um segundo clique e devolve ao APX todo o espaço
  reservado por essa geração.

A retoma valida computador, disco, energia, p1-p4, PARTUUID, tipo GPT, label,
tamanho, contratos, marcador do instalador, caminho UEFI e os três SWM. Cria e
verifica integralmente uma nova cópia de `boot.wim` e substitui apenas esse
ficheiro de forma atómica. Não executa `mkfs`, `blkdiscard`, alteração GPT ou
reinício. Depois de a imagem estar publicada, o finalizador existente arma uma
única entrada APX Setup; a eventual formatação continua limitada a p3 e é feita
pelo WinPE autenticado.

A eliminação de uma criação incompleta reutiliza o executor offline assinado.
Antes do reinício, a operação pendente só muda de create para delete depois de
a UKI e o BootNext temporário estarem confirmados. Se essa transição falhar, o
marcador original é restaurado e os artefactos de arranque temporários são
removidos. Uma instalação que já esteja `ready` mantém o botão `APAGAR` normal
e o mesmo caminho offline de devolução de espaço. Se a própria eliminação
offline recusar, o menu apresenta apenas `TENTAR APAGAR`, sem voltar a oferecer
uma retoma da instalação.

Existe um rollout separado que apenas instala no Host o novo contrato, cliente,
serviço, executores e QuickShell. Esse rollout não toca p3/p4 nem reinicia e
ainda não foi executado. Assim, esta secção descreve a implementação atual do
repositório e não afirma que os novos botões já estejam ativos no computador
físico. A suite completa passa 1095 testes, com 11 omissões esperadas.

O rollout foi depois autorizado pelo proprietário e ativado com AC ligado. A
QuickShell confirmou o carregamento da configuração, o serviço do menu ficou
ativo e os executores instalados correspondem à fonte. A operação pendente,
p3/p4 e firmware permaneceram inalterados: sem montagens, sem BootNext e sem
reinício. O backup é
`/var/lib/apx/backups/20260826T182015Z-native-windows-menu-recovery-v1`. Os
botões de recuperação estão agora ativos, mas nenhuma retoma ou eliminação foi
ainda confirmada no menu.
