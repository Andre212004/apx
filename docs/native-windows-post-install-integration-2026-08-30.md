# Integração pós-instalação do Windows nativo

Data: 2026-08-30. Geração física:
`1c5b5631-fb0e-4384-bf6f-b23eb1798f70`.

## Estado concluído

O lifecycle publicou `windows.json` como `ready`, retirou o pending ativo e
manteve o Linux Boot Manager em primeiro lugar. A instalação tem o perfil
normal `andre`; p3 é NTFS `APXWINTARGET` e o Windows Boot Manager autenticado
continua na APX_EFI.

## SUPER+E

O helper anterior arrancava, como demonstra o canal operacional do PowerShell,
mas tentava reservar `WIN+E` através da API global de hotkeys. O shell do
Windows também reserva essa combinação, tornando o resultado dependente do
momento em que Explorer lê `DisabledHotkeys`.

O helper v2 usa `WH_KEYBOARD_LL`, verifica diretamente as teclas Windows
esquerda/direita mais `E`, suprime o evento apenas quando o hook APX está ativo
e invoca o reboot normal. Como o BootOrder permanece Linux-first, o reboot
regressa ao HUB sem alterar permanentemente o firmware. Não existe timeout,
reboot automático ou ação sem tecla. O estado fica em
`%LOCALAPPDATA%\APX\ReturnToHub.log`; o supervisor VBS só reinicia o helper se
o hook terminar com erro.

## Bluetooth

O rádio real é `USB\VID_0BDA&PID_4852` (Realtek). O
`C:\Windows\INF\setupapi.dev.log` prova que Windows Update instalou o pacote
WHQL `rtkfilter.inf` 1.9.1046.3002, criou `RtkBtFilter` e `RtkBtManServ`,
reiniciou o dispositivo e terminou com `Exit status: SUCCESS`. O DriverStore
contém o firmware RTL8852A/RTL8852B e os drivers Bluetooth Microsoft. Não há
evidência de driver ausente; a indisponibilidade observada durante OOBE foi
transitória enquanto o pacote era instalado e aguardava reinício. Não se
substitui nem força outro driver.

## Apresentação no HUB

A descrição do sistema foi reduzida de
`Windows 11 em partição física · 160 GiB · desempenho nativo` para
`Windows 11 · 160 GiB`. A identidade `NATIVO`, tamanho, geração e contrato de
boot permanecem separados e inalterados.

## Rollout físico pendente

A primeira tentativa de publicar o helper v2 recusou antes de escrever: o
`ntfs3` marcou p3 como dirty e não aceitou montagem read-write sem `force`.
`ntfsfix -n` confirmou `$MFT`, `$MFTMirr` e boot sector íntegros. Não se usou
`force`, não se limpou o dirty bit e p3 não foi modificada. O executor live
mantém temporariamente os hashes v1, portanto Windows continua arrancável.

O próximo passo seguro é, no Windows, executar `chkdsk C: /scan` num Terminal
como administrador e escolher **Reiniciar**. Como Linux permanece primeiro no
BootOrder, esse reboot regressa ao HUB. Só então o helper v2 pode ser copiado
com montagem NTFS normal e verificado byte-a-byte antes de instalar os novos
hashes no executor Linux.

## Compatibilidade Secure Boot do executor

Ao tentar abrir o Windows já `ready`, o executor recusou antes de BootNext com
`Secure Boot não está ativo`. A auditoria confirmou que este Host esteve com
Secure Boot desativado durante toda a instalação: `SecureBoot=0`, mas
`SetupMode=0`, chaves APX/Microsoft presentes e ambos os boot managers
assinados. A exigência estrita só ficou alcançável depois da publicação
`ready`, criando uma incompatibilidade nova com o estado físico já suportado.

O executor agora aceita os dois estados coerentes em User Mode: enforcement
ativo ou desativado. Setup Mode e qualquer divergência entre efivars e
`bootctl` continuam fechados. Mesmo sem enforcement, exige assinatura APX do
Linux Boot Manager, assinatura Microsoft do Windows Boot Manager, metadata,
GPT, PARTUUIDs, tamanhos, perfil e driver exatos. Durante o rollout do helper
v2, aceita apenas dois payloads completos conhecidos (v1 físico ou v2 novo),
nunca uma mistura. `--validate-only` passou e confirmou ausência de BootNext.
