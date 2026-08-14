# Environment switch round-trip hardening v2 — 2026-08-12

## Resultado

O percurso repetível `HUB → Work → HUB → Work → HUB` foi provado no Lenovo
físico. O regresso já não depende de o cliente não privilegiado conseguir
executar `hyprctl exit`: depois de autenticar exatamente o processo `apx` do
Environment ativo, o serviço do Host pede ao systemd que pare a unit externa
da geração correta. O supervisor limpa o Work e lança o Hub.

A prova de 12 de agosto observou:

- Work ativo com a geração `23408376-1cfc-4fe2-aeb9-c4f185c5c9c3`;
- aceitação Host de `return.to-hub` e stop da unit
  `apx-graphical-work-23408376.service`;
- `work=stopped`, Hub ativo e ausência do lock da troca;
- uma segunda troca iniciada normalmente pelo menu do Hub às 07:01:03;
- retorno aceito às 07:01:20 e três ciclos adicionais completos às 07:29,
  07:30 e 07:31;
- Hub saudável durante mais de 23 minutos, com todas as verificações periódicas
  classificadas como `healthy`;
- zero machines, locks ou registos ativos depois da saída limpa final;
- quota Btrfs ativa, consistente e sem override de limites.

## Falha anterior

Havia quatro problemas relacionados, mas distintos:

1. `return.to-hub` respondia `accepted`, porém apenas o cliente chamava
   `hyprctl dispatch exit`. Se o cliente não herdasse um ambiente Hyprland
   utilizável, o Work continuava aberto até o failsafe de 120 segundos.
2. O supervisor mantinha `/run/apx/environment-handoff-v1.lock` durante toda a
   sessão do Hub restaurado. O primeiro retorno funcionava, mas a próxima ida
   ao Work era recusada como troca ainda ativa.
3. O reconciliador de boot conhecia apenas o protótipo antigo `hub-ficticio`.
   Após um reboot interrompido, `work` podia ficar falsamente registado como
   `running`, apesar de não existir machine nem estado gráfico ativo.
4. O Hub ainda tinha o atalho legado `Super+M = terminar Hyprland`, enquanto no
   Work `Super+M` significava regressar ao Hub. Repetir a tecla após a transição
   podia encerrar o Hub recém-aberto; o crash observado do portal ocorreu
   durante essa desmontagem e não foi a origem da primeira falha de retorno.

## Fluxo implementado

```text
cliente apx no Work
        │ return.to-hub
        ▼
serviço Host de troca
  valida PID + UID/GID mapeados + cgroup + geração + registo ativo + lock
        │ systemctl --no-block stop <unit exata da geração>
        ▼
supervisor já existente
  recupera Work → confirma tty1 limpo → remove o próprio lock por inode
        │
        ▼
Hub autenticado
  publica identidade → aceita imediatamente uma próxima troca
```

O cliente não recebe poder adicional. Continua sem comando arbitrário e só
pode pedir a operação tipada. O alvo de stop é construído de um nome validado
e da geração lida de um `registration.json` root-owned; não vem do payload do
cliente. A admissão continua a exigir a linhagem exata da sessão gráfica ativa.

## Concorrência e recuperação

O supervisor fecha e remove o seu lock antes de esperar pela sessão do Hub.
A remoção compara device e inode: um supervisor antigo nunca pode apagar o
lock criado por uma troca mais recente. O failsafe do Work continua armado por
120 segundos e recupera a sessão se o caminho normal não terminar.

No boot, o autostart percorre os registos root-owned com role
`graphical-base`, release `hyprland-base-v2` e estado `running`. Sem machines
ativas, recupera cada registo antes de lançar o Hub. Identidades ou ownership
inesperados falham fechados em vez de serem reparados silenciosamente.

## Interface

- no Work, o botão pede o retorno normal e tipado ao Hub;
- depois da primeira aceitação, o botão fica em estado pendente e evita pedidos
  repetidos durante a desmontagem;
- uma recusa aparece no painel em vez de desaparecer no stderr;
- por escolha posterior do proprietário, `Super+E` termina diretamente apenas
  o compositor e fornece uma fuga independente para recuperação;
- `Super+M` abre o menu mas não executa transições; `Super+F` abre o gestor de ficheiros;
- cada aceitação ou recusa é registada no journal com operação e peer PID, sem
  payload sensível.

## Instalação e rollback

As versões anteriores foram preservadas em
`/var/lib/apx/environment-switch-v1/backups-20260812-host-driven-return-v2/`.
Esse diretório contém serviço, cliente, supervisor, autostart, runtime e as
cópias anteriores das configurações privadas de Hub e Work.

Rollback é uma operação de recuperação, não um passo normal: fazê-lo apenas em
tty1, sem machine ativa, copiando de volta os ficheiros correspondentes,
reiniciando `apx-environment-switch-v1.service` e confirmando hashes, catálogo,
units falhadas, quota e ausência de resíduos. Não restaurar apenas uma parte,
porque serviço, cliente, supervisor, hashes do seed e interface formam um
contrato único.

## Diagnóstico rápido

Estado saudável no Hub:

- `machinectl list --no-legend` mostra apenas `apx-hub`;
- existe `/run/apx/official-hub-graphical-v1.json`;
- não existem `environment-handoff-v1.lock` nem
  `active-graphical-environment-v1.json`;
- Hub está `running` e Work `stopped` nos registos;
- `systemctl --failed --no-legend` não apresenta units.

Durante Work, a machine e o registo ativo devem apontar para a mesma geração e
o lock deve existir. Uma recusa é consultável com:

```bash
journalctl -u apx-environment-switch-v1.service -b --no-pager
```

Não apagar locks nem editar `registration.json` manualmente. Em falha visual,
usar `Ctrl+Alt+F1`, deixar o failsafe terminar e inspecionar journal, machines e
registos antes de qualquer recuperação manual.

## Validação

A regressão de repositório passa 1019 testes com 11 skips esperados de hardware
ou condições externas. Os testes cobrem o stop Host-driven, logs, ausência do
`hyprctl` no cliente, lock associado ao inode, reconciliação de múltiplos
workloads, feedback da QuickShell e hashes do seed gráfico. O reboot físico do
novo reconciliador genérico não foi provocado apenas para obter evidência; essa
parte está instalada e testada em unidade, mas continua pendente de observação
no próximo reboot normal.

Depois do checkpoint limpo, o Hub foi lançado novamente e usado nos ciclos
adicionais. O estado entregue após a saída limpa das 07:34 é Hub e Work
`stopped`, tty1 livre, serviço de troca ativo, sem lock de handoff e sem units
Host falhadas.

## Decisão posterior de atalhos

O proprietário rejeitou `Super+M` como controlo de Environments e pediu uma
forma memorizável de voltar à recuperação do Host quando a interface ou o
serviço tiver problemas. O contrato final deste piloto é:

- botão Environments: troca normal, autenticada e observável;
- `Super+E`: saída direta do compositor, independente do serviço de troca;
- `Super+F`: ficheiros;
- `Super+M`: abre o menu de Environments, sem executar uma transição direta;
- `Ctrl+Alt+F1`: mudança visual direta para tty1 continua disponível.

No Work, a saída direta ainda é observada pelo supervisor Host, que limpa a
machine e restaura o Hub. No Hub, a mesma saída recupera tty1. Assim o atalho
não concede comandos Host ao Environment: apenas termina o seu compositor.

O caminho direto Hub → tty1 foi fisicamente observado às 10:10:50, depois de
mais de duas horas de watchdogs saudáveis, sem pedido `return.to-hub` nesse
instante. Duas tentativas automatizadas de provar Work → Hub diretamente foram
antecipadas por ativações normais do botão às 07:43:30 e 10:13:11. Por isso, a
instalação, os bindings e a cobertura de testes estão confirmados, mas o toque
físico `Super+E` dentro do Work continua pendente de observação numa utilização
normal; não é apresentado aqui como prova concluída.

### Clarificação de atalhos e continuidade — 2026-08-13

Decisão final posterior no mesmo dia: o proprietário inverteu os dois atalhos.
`Super+E` abre agora o menu de Environments; `Super+M` executa a saída interna
do Hyprland. Na Central de Controlo do Hub, “Escolher Environment” foi
substituído por “Sair para o Host”. O botão central da barra continua a abrir o
menu de Environments. Esta decisão substitui a atribuição E/M descrita nos
parágrafos históricos abaixo.

O arranque da shell deixou também de esperar quatro segundos fixos. O launcher
espera duas observações consecutivas de um monitor Hyprland ativo, separadas
por 50 ms e limitadas a dois segundos. A QuickShell real demorou cerca de 0,5 s
a carregar; no caminho normal são removidos aproximadamente 3,9 s de atraso
artificial sem eliminar a barreira contra a corrida de portal/layer-shell.

O contrato final distingue três ações:

- `Super+H` abre ou reanexa o único PTY persistente do Host; fechar a janela
  apenas desanexa e não cria outro Codex; se a janela já existir, o atalho
  limita-se a focá-la;
- `Super+E` usa o dispatcher interno `hl.dsp.exit()` e não depende do socket
  IPC, da QuickShell ou dos serviços APX;
- `Super+M` abre o menu de Environments, sem sair nem iniciar diretamente uma
  transição.

O menu de Environments está no `Super+M`, no botão central da barra e numa
entrada explícita da Central de Controlo. A Central identifica o terminal como
“Terminal do Host · sessão única” e mostra o atalho `Super+H`.

Um diagnóstico encontrou ainda uma armadilha: uma sessão temporária
`machinectl shell apx@...` durante o desktop ativo faz logind criar e depois
desmontar `/run/user/1000` quando essa sessão termina, apagando os sockets do
Hyprland e da QuickShell. Diagnósticos futuros não podem abrir logins do
utilizador dentro de um Environment gráfico ativo; devem usar o namespace do
PID existente ou leituras root que não criem uma sessão logind.
