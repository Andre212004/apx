# Windows nativo em 120 GiB — checkpoint físico de 2026-08-25

## Resultado já instalado

- A criação de Environments APX deixou de fazer uma atualização parcial de
  Arch. A instalação adicional usa `pacman -Syu`, e uma criação gráfica real
  descartável completou, publicou e foi destruída corretamente.
- Os clones falhados e nunca publicados `faculdade` e `xasso` foram limpos pelo
  contrato de recuperação; nenhum Environment publicado foi apagado.
- O catálogo do Hub contém uma entrada independente com nome visível
  `Windows`, tipo `native-boot`, etiqueta `NATIVO` e reserva declarada de
  120 GiB. Enquanto o Windows Boot Manager ainda não existir, a linha mostra
  `A PREPARAR` e não pode ser aberta ou apagada.
- Windows e Ubuntu virtualizados deixaram de ser opções no formulário normal
  de criação. Environments normais continuam a ser APX nativos sobre o kernel
  do Host.
- O caminho futuro de abertura usa `bootctl set-oneshot auto-windows` num
  executor root fixo e reinicia. O default permanente continua a ser
  `apx-secure-boot-v1.conf`; não existe QEMU, guest agent ou Looking Glass.

## Instalação interna sem pen concluída

Como o proprietário não dispõe de uma pen USB, os 120 GiB reservados foram
divididos temporariamente em dois blocos, sem tocar nas partições APX:

- 111 GiB continuam como espaço não alocado, destino exclusivo do Windows;
- 9 GiB formam a partição FAT32 `APX_WINSETUP`, que contém o instalador.

O `install.wim` original foi dividido em três ficheiros SWM compatíveis com
FAT32. A validação confirmou os hashes de `bootx64.efi` e `boot.wim`, as três
partes SWM, 11 imagens Windows em `pt-PT` e a assinatura Microsoft Windows
Production PCA 2011. Secure Boot continua ativo: a chave APX original continua
confiada e foram acrescentadas as autoridades Microsoft necessárias. Os três
carregadores APX passam a verificação direta com o certificado APX original.

O diagnóstico dentro do WinPE confirmou que `Disk 0` aparece com 476 GB e
111 GB livres. O erro `0x80070103` ao voltar a carregar `stornvme.inf` não
significa ausência do NVMe: o controlador Microsoft já estava carregado. A
mensagem posterior sobre um controlador de multimédia era o erro genérico do
Setup depois de perder acesso aos próprios ficheiros de instalação. A causa
era a partição interna estar corretamente marcada como ESP: o firmware e o
WinPE conseguiam arrancar dela, mas o WinPE não lhe atribuía uma letra.

Uma primeira correção tentou usar `DiskPart assign`; o arranque físico mostrou
um terminal de recuperação porque o Windows proíbe atribuir uma letra dessa
forma a uma partição GPT que não seja `basic data`. O utilizador fechou o
terminal e o WinPE regressou ao APX sem qualquer alteração de partições.

O índice de Setup de `boot.wim` foi reconstruído novamente com o mecanismo
específico do Windows para uma ESP: executa `wpeinit`, procura primeiro uma
origem já montada e, se necessário, usa `mountvol W: /S`. Só aceita a origem
que contenha `setup.exe` e as três partes SWM e abre o Setup a partir dela. Não
usa DiskPart e não cria, apaga, altera ou formata partições. A imagem instalada
passou verificação integral e os dois ficheiros incorporados foram extraídos e
comparados byte a byte. O SHA-256 atual de `boot.wim` é
`b4041a17b34aca0db72e32eb1bcd7d675354f600d4b79efb2ab4a8af8dcb5df2`.

A entrada UEFI `APX Windows Setup` aponta exclusivamente para a partição 3 e
foi criada fora da ordem permanente. `BootOrder` permanece
`2001,0005,0000,2002,2003`, o APX continua a ser o arranque atual e não existe
`BootNext`. O executor
`scripts/physical-pilot/boot-native-windows-internal-installer-v1.sh` volta a
validar hardware, alimentação, GPT, partição, hashes, assinatura, UEFI e ordem
de arranque antes de definir apenas o próximo arranque e reiniciar.

## Armazenamento físico concluído

Disco físico vinculado: `/dev/nvme0n1`, Samsung serial
`S4DYNX0R253702`, GPT `AC9FC0BD-2162-43A9-AAE6-3F654FF6F275`.

O scrub integral dos dados usados terminou sem erros atuais. A redução offline
assinada preservou o início e a identidade da partição APX:

- APX LUKS p2 anterior: setores `2099200..1000215182`;
- APX LUKS p2 atual: setores `2099200..748556287`;
- espaço inicialmente libertado: setores `748556288..1000215182`;
- espaço reservado: `128849354240` bytes, ou `120.0003 GiB`.

O método online foi retirado. A UKI de manutenção assinada reduziu Btrfs com o
filesystem desmontado, fechou dm-crypt e só então reduziu GPT. O primeiro
arranque instrumentado revelou a ausência de `vfat`; o seguinte revelou que o
ESP ainda estava montado durante `sfdisk`. Ambos falharam antes da escrita GPT
e preservaram um estado recuperável. A versão final incorporou `vfat`,
desmontou o ESP antes da alteração e gravou
`success:128849354240`. No arranque normal seguinte foram confirmados:

- p2: `382186029056` bytes;
- dm-crypt: `746424320` setores;
- Btrfs: `382169251840` bytes e zero slack;
- erros atuais de escrita, leitura, flush e geração: zero.

O marcador root-only
`/var/lib/apx/native-environments/windows-storage-v1.json` está instalado. O
Hub já reconhece a reserva; a entrada continua `A PREPARAR` apenas porque o
Windows Boot Manager ainda não existe.

## Passos exatos do utilizador

1. Com o carregador ligado, o APX executa o comando protegido com `--reboot`.
   O arranque é único; não é necessário abrir o menu F12 nem pressionar uma
   tecla para arrancar por CD. O WinPE expõe automaticamente o instalador como
   `W:` e abre a instalação; não é necessário usar `Shift+F10`, `drvload` ou
   procurar qualquer controlador.
2. No instalador português, escolher idioma/teclado, `Instalar agora` e aceitar
   a licença. Se a edição não for escolhida automaticamente pela chave OEM já
   presente no firmware, selecionar apenas a edição correspondente à licença
   do computador. Não introduzir nem publicar a chave OEM.
3. Escolher `Personalizada: instalar apenas o Windows (avançado)`.
4. Na tabela de discos, selecionar somente `Espaço não alocado na Unidade 0`,
   com aproximadamente 111 GB, e carregar em `Seguinte`. Deixar o instalador
   criar as suas partições nesse espaço.
5. Nunca apagar, formatar ou selecionar `APX_EFI` (1 GB), `APX_CRYPT`
   (aproximadamente 356 GB) ou `APX_WINSETUP` (9 GB). Se o espaço não alocado
   de aproximadamente 111 GB não aparecer exatamente uma vez, parar e voltar
   ao APX sem alterar partições.
6. Deixar a instalação reiniciar o computador as vezes necessárias. Não voltar
   a escolher `APX Windows Setup`. Se o APX abrir antes de a instalação acabar,
   parar e pedir ao APX para encaminhar uma vez para o novo Windows Boot
   Manager; não repetir a instalação.
7. Depois de chegar ao ambiente de trabalho do Windows, reiniciar e, no logótipo
   Lenovo, usar `F12` (ou `Fn+F12`) para escolher `Linux Boot Manager` uma única
   vez caso o Windows tenha passado a ser o default. Já no Hub, o APX valida o
   Windows Boot Manager, repõe o APX como default permanente e transforma
   `Windows · NATIVO` em `PRONTO`.
8. No Windows não existe `SUPER+E`: é outro sistema operativo, não uma VM. Um
   reinício normal regressará ao APX depois de o default ser finalizado. Não é
   preciso instalar guest tools, Looking Glass, QEMU ou qualquer agente APX no
   Windows.

A palavra-passe do disco APX não deve ser removida. Ela protege apenas a
partição Linux cifrada e não impede o instalador Windows de usar os 111 GiB não
alocados. No arranque do APX continua a ser necessário introduzi-la e carregar
Enter.

## Windows instalado e Wi-Fi preparado offline

O Setup consumiu somente o bloco reservado e criou MSR de 16 MiB, Windows NTFS
de 110,2 GiB e Recovery de 790 MiB. A antiga partição de instalação é agora p6
e contém também o Windows Boot Manager; APX_EFI p1 e APX_CRYPT p2 mantêm as
identidades e tamanhos anteriores.

O OOBE chegou à página de rede mas não tinha o controlador do Realtek
RTL8852AE físico (`10ec:8852`, subsistema Lenovo `17aa:4852`). O pacote oficial
Lenovo Windows 11 DS551503 foi descarregado com o SHA-256 publicado
`1defff5645c18427c5f1af5af07a0ebae1dde25c70c3624869d485cef06f0c04`.
Foi extraído somente o conjunto Realtek `6001.0.10.340`; o INF contém o ID
exato `PCI\VEN_10EC&DEV_8852&SUBSYS_485217AA` e o catálogo PKCS#7 identifica
`Microsoft Windows Hardware Compatibility Publisher`.

Os quatro ficheiros foram copiados atomicamente e verificados em
`C:\APX\Drivers\Realtek8852AE`. No OOBE, carregar em `Instalar controlador`,
procurar essa pasta no disco Windows C: e confirmar. Não é necessário executar
o pacote Lenovo nem descarregar nada no Windows.

A ordem UEFI permanente é agora
`0005,0006,0000,2001,2002,2003`: Linux Boot Manager primeiro e Windows Boot
Manager segundo. O executor OOBE valida o hardware, GPT, ambas as partições
Windows, o Boot Manager/BCD, Secure Boot e todos os ficheiros do driver antes
de definir apenas `BootNext=0006`. Reinícios normais regressam ao APX depois de
terminadas as continuações temporárias do Setup.

## Evidência

- Suite completa depois do staging Wi-Fi e executor OOBE: 1078 testes, 11
  ignorados, zero
  falhas.
- Backup do catálogo inicial:
  `/var/lib/apx/backups/20260825-native-windows-catalog-v1`.
- Backups das revisões do serviço:
  `/var/lib/apx/backups/20260825-native-windows-storage-awareness-v1` e
  `/var/lib/apx/backups/20260825-native-windows-storage-awareness-v2`.
- Estado de recuperação preservado: duas operações antigas e não relacionadas
  continuam classificadas como `preserve-and-inspect`; não foram limpas por
  esta alteração.
- Backup do instalador interno e da UEFI:
  `/var/lib/apx/backups/20260825-native-windows-internal-installer-v5`.
- Backup da extensão Secure Boot:
  `/var/lib/apx/backups/20260825-native-windows-secure-boot-v1`.
- Backups e evidência das correções WinPE:
  `/var/lib/apx/backups/20260825-native-windows-winpe-media-v1` e
  `/var/lib/apx/backups/20260825-native-windows-winpe-media-v2`.
- Backup e evidência do driver Wi-Fi:
  `/var/lib/apx/backups/20260825-native-windows-wifi-driver-v1`.
