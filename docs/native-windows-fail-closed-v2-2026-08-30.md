# Lifecycle Windows fail-closed — incidente e recuperação de 2026-08-30

## Resultado

O APX/Linux voltou a ser o caminho de arranque seguro e permanece primeiro na
`BootOrder`. Não existe `BootNext`. O finalizador Windows instalado é oneshot,
não tem política `Restart=` e não contém qualquer caminho que arme `BootNext`
ou execute reboot. A presença isolada de `windows-pending.json` nunca autoriza
um novo arranque Windows.

A geração afetada, `18fe09c4-ed14-40a3-96d2-544d3ba3e628`, está em
`recovery-required`. O original recuperado manualmente continua preservado em
`/var/lib/apx/native-environments/windows-pending.json.recovery-20260830`; o
primeiro diagnóstico terminal foi ainda arquivado em
`windows-failures/<generation>/failure.json`. Nenhum destes ficheiros deve ser
apagado até a recuperação Windows ser concluída ou explicitamente descartada.

## Evidência e causa raiz

O WinPE parou depois da formatação autenticada de p3 com
`APX-FORMAT-04 / formatted-target-label` e repetiu
`The system cannot find the batch label specified - file_contains`.

O `apx-media.cmd` incorporado no índice 2 de `boot.wim` coincidia com o ativo
instalado. As nove chamadas a `:file_contains` e o próprio label existiam, mas
o ficheiro tinha 361 linhas terminadas apenas por LF, sem um único CRLF. O
`cmd.exe` do WinPE não conseguiu despachar o subprograma. O WinPE contém
`find.exe`, mas não contém `findstr.exe`. A correção remove o subprograma
problemático, usa diretamente o `find.exe` autenticado do WinPE e impõe CRLF
por `.gitattributes` e testes de bytes.

O erro tornou-se indisponibilidade Linux por uma segunda falha independente:
o handler terminal não deixou `install-status-v2.ini` em p4 nem na APX ESP, e o
finalizador interpretava `stage=installing` sem Windows completo como ordem
para rearmar APX Windows Setup, incrementar `resume_attempts` e reiniciar. O
estado chegou a 11 tentativas. A condição systemd verificava apenas a existência
do pending, convertendo uma falha WinPE numa sequência de reboots.

## Máquina de estados atual

Estados de criação persistentes:

- `maintenance`: transformação GPT offline ainda autenticada;
- `preparing-installer`: preparação do suporte, sem armar firmware;
- `prepared`: suporte pronto, Linux seguro, aguarda ação explícita;
- `installing`: uma ação explícita arrancou o WinPE uma única vez;
- `boot-prepared`: WinPE aplicou Windows e publicou o mesmo status em p4 e p1;
- `finalizing`: validação completa e publicação transacional dos metadados;
- `failed`: erro terminal autenticado do WinPE;
- `recovery-required`: ausência, incoerência ou ambiguidade de evidência.

`complete` é representado pela publicação atómica de `windows.json` e remoção
do pending. Falhas nunca removem evidência. `failed` e `recovery-required` são
idempotentes: limpam qualquer BootNext, confirmam a entrada Linux exata em
primeiro e regressam sem reboot.

As únicas retomas são ações explícitas do menu. Têm contador separado
`explicit_attempts`, limitado a duas. O contador histórico `resume_attempts`
é preservado como evidência e não concede autorização. Uma retoma valida
computador, serial e GUID GPT do disco, geometria e PARTUUIDs, energia, estado
do serviço, ausência de BootNext e a entrada UEFI exata antes de armar um único
boot. Qualquer ambiguidade falha fechado e restaura o pending anterior.

Um sucesso WinPE capaz de autorizar o primeiro boot do Windows exige dois
markers byte a byte idênticos: p4/APX e p1/EFI/APX. Uma falha só reduz
privilégio e pode ser consumida com a identidade da partição setup e a geração
correta. O handler fatal tenta publicar em ambos os locais e preserva o log em
p4.

## Diagnóstico do Windows desta geração

Layout físico verificado em 2026-08-30:

| Papel | Dispositivo | Início/setores | PARTUUID | FS/label |
| --- | --- | ---: | --- | --- |
| APX EFI | `/dev/nvme0n1p1` | `2048 / 2097152` | `9625F250-9ACC-453A-AE63-0C863ADE440F` | FAT32 `APX_EFI` |
| APX LUKS | `/dev/nvme0n1p2` | `2099200 / 662571008` | `8835C8F0-F02F-4FC2-9035-5DBBC191DF9E` | LUKS2 |
| Windows alvo | `/dev/nvme0n1p3` | `664670208 / 316669952` | `099C31D8-313A-4ABA-B0E0-2B59502C9674` | NTFS `APXWINTARGET` |
| Setup | `/dev/nvme0n1p4` | `981340160 / 18874368` | `309BEBB6-5C32-4E21-9C92-6D758E51389D` | FAT32 `APXWINSETUP` |

O disco físico tem GUID `AC9FC0BD-2162-43A9-AAE6-3F654FF6F275` e serial
`S4DYNX0R253702`. p3 está marcada dirty, mas a sondagem read-only confirmou
MFT/MFTMirr e boot sector alternativo. Está 99,9% livre e contém apenas
`APX/install-contract-v2.ini`: não existem `Windows`, registry hives,
`Users`, `ProgramData` APX nem `Windows/System32/winload.efi`. Assim, esta
geração parou antes de DISM `/Apply-Image`; não existe Windows instalado que
possa ser recuperado apenas com BCDBoot/BCD.

p4 está íntegra e contém os três SWM e o boot do instalador. Os BCD EFI/BIOS de
p4 apontam para `sources/boot.wim` e para o loader de Windows Setup; não são um
BCD de uma instalação em p3. p1 não contém `EFI/Microsoft`, e o firmware não
tem `Windows Boot Manager`. `Boot0000 APX Windows Setup` aponta exatamente
para p4; `Boot0005 Linux Boot Manager` aponta para p1 e está primeiro.

Conclusão: é necessário repetir a aplicação da imagem sobre a mesma partição
alvo autenticada, não “reparar” uma instalação existente. Isso só pode ser
feito depois de reconstruir `boot.wim` com o batch CRLF corrigido e através de
uma tentativa explícita. Preparar o suporte não arma firmware nem reinicia.

## Runbook de recuperação

1. Confirmar que Linux é `BootCurrent`, primeiro em `BootOrder`, sem
   `BootNext`, e que o finalizador terminou com `Result=success`.
2. Preservar o pending, o `.recovery-20260830`, o failure archive, o contrato
   e os status/logs WinPE. Não editar p3/p4 manualmente.
3. Correr a suite e confirmar que o batch de origem é CRLF, não contém
   `file_contains`/`findstr`, contém `find.exe` e publica falhas em p4/p1.
4. Usar apenas a ação explícita `retry` do menu. Ela revalida identidades,
   reconstrói e verifica o `boot.wim`, incrementa `explicit_attempts` e arma
   exatamente uma vez `APX Windows Setup`.
5. Se WinPE falhar, arrancar Linux normalmente. O finalizador consome o erro
   para `failed`; sem status, usa `recovery-required`. Nunca volta a arrancar
   Windows sozinho.
6. Se WinPE publicar `boot-prepared` espelhado, confirmar explicitamente o
   primeiro boot Windows. Linux continua primeiro na ordem permanente.
7. Publicar `windows.json` apenas depois de `windows_complete()` confirmar
   loader, perfil real, integração APX, driver Wi-Fi, EFI Microsoft assinada,
   BCD e uma única entrada firmware coerente.

Para recuperação externa, arrancar um live Linux, abrir LUKS, montar `@apx` em
`/var/lib/apx`, renomear reversivelmente o pending e limpar BootNext. Nunca
eliminar partições para interromper uma retoma. O ficheiro renomeado deve ser
preservado como evidência e reintroduzido apenas depois de instalar um
finalizador fail-closed.

## Testes de regressão

`tests/test_apx_native_windows_lifecycle_safety.py` reproduz o incidente exato:
`create/installing`, `resume_attempts=11` e status terminal
`APX-FORMAT-04`. O resultado obrigatório é `failed`, com evidência preservada,
sem chamada a reboot nem armamento de BootNext. Há ainda cobertura para status
ausente, BootNext já inexistente, limite de duas retomas explícitas, ausência
de `Restart=` no serviço, preparação sem reboot e bytes CRLF do WinPE.

Foi ainda reconstruída uma cópia temporária do `boot.wim` físico com os três
ativos atuais, executado `wimlib-imagex verify` sobre os dois índices e
extraído novamente o batch/contrato. Os bytes extraídos coincidiram com as
fontes; SHA-256 da WIM resultante de ensaio:
`5b10d3698cccec187a126317c9c94157568f0dccf4cdd3cd9ce85353d6c57d65`.
A p4 esteve montada apenas read-only, a cópia temporária foi removida e
BootCurrent/BootOrder/ausência de BootNext permaneceram inalterados.
