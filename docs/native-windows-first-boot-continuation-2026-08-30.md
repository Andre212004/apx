# Windows nativo: continuação explícita do primeiro arranque

Data: 2026-08-30. Geração observada:
`1c5b5631-fb0e-4384-bf6f-b23eb1798f70`.

## Diagnóstico

O WinPE concluiu a aplicação do índice 6, instalou o driver Realtek, executou
`bcdboot` e publicou `boot-prepared` de forma idêntica em p4 e APX_EFI. O
primeiro arranque do Windows iniciou os serviços essenciais do OOBE e terminou
a fase 4 com código `0`. O próprio `windeploy.exe` registou
`reboot requested flag [True]` e explicou que precisava reiniciar antes de
abrir o OOBE. Não existe crash dump.

O regresso ao Linux foi, portanto, o efeito correto do BootNext único: depois
de consumido, um reboot pedido pelo Windows segue novamente o BootOrder
permanente, cujo primeiro elemento é Linux. A falha estava no contador APX.
`explicit_attempts` limitava a dois a soma do arranque WinPE e dos arranques
Windows, embora sejam fases e riscos diferentes. Uma instalação bem-sucedida
consumia uma tentativa no WinPE e o primeiro boot consumia a segunda, ocultando
o botão quando o Windows solicitava o reboot normal anterior ao OOBE.

## Contrato corrigido

- tentativas WinPE continuam limitadas a duas;
- continuações de `boot-prepared` têm um contador separado, limitado a oito;
- nenhuma continuação é automática;
- cada clique revalida Host, energia, p3 NTFS/PARTUUID, status espelhado da
  geração, Windows Boot Manager e ausência de BootNext;
- cada clique arma apenas um BootNext para Windows e não altera BootOrder;
- `boot-prepared` nunca reconstrói p4 nem volta a executar WinPE;
- ao atingir o limite, a operação permanece recuperável sem reboot automático;
- o menu distingue `PROSSEGUIR WINDOWS` de `RETOMAR WINDOWS`.

O limite inicial de quatro revelou-se insuficiente na execução física: o OOBE
concluiu com `IMAGE_STATE_COMPLETE`, mas uma atualização ZDP instalou
`KB5121003`, marcou reboot obrigatório e devolveu corretamente ao Linux depois
de consumir o BootNext único. O Windows documenta reinícios durante OOBE para
ZDP, alterações de idioma e atualizações do sistema. O orçamento passou para
oito cliques explícitos; não existe loop nem rearmamento automático.

O mesmo post-mortem encontrou `SetupComplete.cmd` com exit `1`, embora o
`pnputil` tenha registado que `netrtwlane6.inf` já existia e estava atualizado
no dispositivo. O provisioning passou a aceitar esse resultado apenas depois
de uma segunda verificação independente em `pnputil /enum-drivers /files`,
registando `hardware.warning` e `hardware.complete`. Uma ausência real do INF
continua terminal em `hardware.failed`.

Para a geração física observada, o journal demonstra uma aplicação WinPE e
uma continuação Windows. A migração lógica preserva o pending original num
backup root-only e representa esse histórico como `explicit_attempts=1` e
`boot_attempts=1`. Não modifica p1, p3, p4, BCD ou firmware.

## Próxima ação física

Depois de instalar e validar esta correção, o proprietário pode usar
`PROSSEGUIR WINDOWS`. O esperado é o Windows continuar o OOBE já aplicado. Se
o Windows pedir outro reboot durante a preparação, o Linux volta a aparecer e
o mesmo botão continua disponível dentro do limite. Não usar `CRIAR ENVIRONMENT`:
isso inicia uma geração nova e reaplica a imagem desde o princípio.
