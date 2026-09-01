# Segunda tentativa física Windows: post-mortem fail-closed

Data: 2026-08-30. Geração: `18fe09c4-ed14-40a3-96d2-544d3ba3e628`.

## Resultado

A proteção introduzida em `90a92b1882811d33b236af2c505bc75f125b6f72`
funcionou: o único `BootNext` foi consumido, o WinPE publicou uma falha
terminal em `APXWINSETUP`, o Linux voltou a arrancar por `Boot0005`, e o
finalizador converteu `installing` em `failed` sem rearmar firmware nem
reiniciar.

O erro terminal foi `APX-PART-03`, etapa `partition-identities`, detalhe
`windows-target`. O log preservado em p4 demonstra a sequência:

1. o WinPE iniciou;
2. o disco GPT exato foi encontrado como Disk 0;
3. p4 `APXWINSETUP` foi encontrada e montada temporariamente em `W:`;
4. o contrato de p4 foi validado;
5. p1 `APX_EFI` e p2 `APX_CRYPT` foram localizadas;
6. a enumeração de p3 falhou antes de lhe atribuir uma letra;
7. o status terminal foi escrito em p4 e o WinPE regressou ao Linux;
8. o finalizador classificou a operação como `failed` às 20:43:26 WEST.

p3 permaneceu intacta: contém apenas `APX/install-contract-v2.ini`, com mtime
de 2026-08-26. Não existem `Windows`, `Windows/System32`, `winload.efi`, hives
de registry, `Users` ou `ProgramData`. Nem a consulta DISM do índice, nem
`Apply-Image`, nem `bcdboot` foram alcançados. p1 não contém `EFI/Microsoft`, e
o firmware não contém Windows Boot Manager. A alteração de mtime do BCD de p4
às 20:41:12 pertence ao arranque do próprio suporte WinPE, não a `bcdboot`,
cujo destino seria p1.

## Causa raiz

O batch procurava o label completo `APXWINTARGET` dentro da tabela produzida
por `diskpart detail partition`/`list partition`. Esse label tem 12
caracteres; a coluna tabular `Label` do DiskPart expõe apenas 11. Os labels que
passaram antes da falha tinham 11 (`APXWINSETUP`) e 7 (`APX_EFI`) caracteres.
Assim, a candidata p3 correta não incrementava `APX_PART_COUNT`, apesar de o
tipo GPT, tamanho, PARTUUID e filesystem observados pelo Linux continuarem
exatos.

O desenho corrigido não confia no label tabular truncado. Dentro do disco já
autenticado por GUID e tamanho, exige uma única candidata Microsoft Basic
Data com o tamanho contratado. Só depois a monta temporariamente, valida o
label completo com `vol`, e compara byte a byte o contrato em p3 com o
contrato incorporado no WinPE. A revalidação imediatamente anterior ao
`format` repete a descoberta, exige o mesmo número de partição e volta a
comparar o contrato. Portanto a correção não reduz as condições necessárias
para autorizar a única operação destrutiva.

## Lacunas de observabilidade encontradas

O status v2 anterior continha apenas código e etapa. A saída de DiskPart era
reutilizada em `X:` e perdida no reboot. Além disso, p1 só seria montada depois
da descoberta de p3, logo esta falha não podia ser espelhada em APX_EFI. O
arquivo Linux preservava apenas a primeira falha de uma geração, ocultando
falhas explícitas posteriores.

Antes de outra tentativa, o código passa a:

- registar, por partição candidata, exit code do DiskPart e resultados de
  tipo, tamanho e label, incluindo a saída bruta;
- montar e autenticar APX_EFI antes de procurar p3;
- incluir `detail`, `command`, `exit_code` e `diagnostic` no status terminal;
- copiar status e log terminal byte a byte para p4 e APX_EFI;
- guardar stdout/stderr no log persistente e um `dism-apply-v2.log` dedicado;
- registar exit codes de format, DISM e bcdboot;
- exigir uma tecla em falha, mantendo a mensagem visível antes do regresso ao
  Linux;
- arquivar cada falha explícita de forma imutável, preservando também o
  primeiro `failure.json` por compatibilidade.

Estas alterações ficam apenas no repositório e nos ficheiros Linux instalados
até existir uma decisão explícita de preparar uma terceira tentativa. Este
post-mortem não autoriza reconstruir p4, armar BootNext, formatar ou reiniciar.

## Preparação da próxima tentativa pelo APX Hub

Depois do post-mortem, o proprietário autorizou preparar o percurso interativo
do Hub, mantendo o próprio clique como fronteira de autorização. O estado
terminal `failed` passa a expor `RETOMAR WINDOWS` quando a geração continua
autenticada, não existe operação concorrente e ainda resta uma tentativa
explícita. Tornar o botão visível não altera p3/p4 nem o firmware.

Ao clicar, o executor usa a mesma geração, volta a validar AC, bateria, Host,
disco, GPT e UEFI, reconstrói e verifica p4 com o batch corrigido e só depois
arma um único BootNext para APX Windows Setup. A contagem passa de 1/2 para
2/2. Qualquer falha anterior ao reboot restaura o pending original e limpa
BootNext; qualquer falha WinPE regressa ao Linux e fica terminal, sem nova
retoma automática.
