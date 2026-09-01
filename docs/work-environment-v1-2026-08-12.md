# Work Environment v1 — 2026-08-12

Atualização de atalhos em 2026-08-13: `Super+E` abre o menu de Environments e
`Super+M` é a saída interna de emergência do compositor. Esta decisão
substitui a atribuição E/M histórica abaixo. O arranque da QuickShell passou de
uma espera fixa de quatro segundos para duas verificações reais de prontidão do
monitor, normalmente cerca de 0,1 s antes do carregamento da interface.

## Resultado físico

O Environment `work`, apresentado ao utilizador como **Work**, foi criado a
partir da release selada `hyprland-base-v2`, com role `graphical-base`. Não é
uma cópia do Hub: tem root e home Btrfs próprios, catálogo próprio e não recebe
os controlos privilegiados do Host que pertencem ao Hub.

O primeiro percurso físico foi concluído: o Work chegou ao Hyprland e manteve a
sessão gráfica ativa durante cerca de 42 segundos, com Waybar e os serviços do
desktop em execução. A saída foi limpa e o supervisor iniciou o Hub logo a
seguir. No final da prova ambos foram encerrados localmente e tty1 ficou livre.

Identidade registada:

- nome interno: `work`;
- nome visível: `Work`;
- categoria: `work`;
- release: `hyprland-base-v2`;
- generation: `23408376-1cfc-4fe2-aeb9-c4f185c5c9c3`;
- root: subvolume Btrfs 320, limite 32 GiB;
- home: subvolume Btrfs 321, limite 64 GiB;
- política de atualização: `follow-host`;
- restauro de sessão: desativado nesta versão.

## Desktop normal do Work

O Work tem Hyprland com a linguagem visual escura/ciano do Hub, mas sem fingir
ser o Hub. A barra identifica `APX · WORK · VOLTAR AO HUB`; o botão faz um
pedido tipado de regresso ao Hub em vez de terminar o compositor diretamente.

Aplicações e integrações disponíveis:

- Rofi como lançador (`Super+D`);
- Thunar com GVFS como gestor de ficheiros (`Super+F`);
- Firefox como navegador (`Super+B`);
- Kitty como terminal (`Super+Return`);
- notificações Mako, agente Polkit, UDisks/Udiskie, portais desktop;
- Flatpak com o remoto Flathub;
- File Roller, Mousepad e Ristretto;
- diretórios Desktop, Downloads, Documents, Music, Pictures, Videos,
  Templates, Public e Projects;
- associações padrão de diretórios ao Thunar e de HTTP/HTTPS/HTML ao Firefox.

O botão regressa normalmente ao Hub. `Super+E` e o alias `Super+Shift+E` são
saídas de emergência diretas do compositor; `Super+M` abre o menu mas não executa a troca. O
Work não contém botões de energia do Host, consola
do Host, atualização coordenada nem administração de outros Environments.

## Botão Environments e ponte viva

No Hub, o botão passa a identificar claramente
`APX · HUB · ENVIRONMENTS`. O menu mostra a identidade atual, o estado dos
Environments, política de sessão e atualização, e permite escolher o Work.
Dentro de um Environment comum o mesmo lugar é contextual: apresenta o nome do
Environment e oferece o regresso ao Hub.

O serviço de troca publica também uma ponte viva em
`/home/.apx-host-bridge/environment-switch-v1.sock`. Isto evita que um restart
do serviço deixe o Hub já montado com um inode de socket antigo. A ponte é
gravável pelo cliente, mas continua num diretório root não gravável e cada
pedido é autenticado por PID, UID, cgroup e identidade gráfica ativa.

Foi provado a partir do namespace e UID do Hub que o cliente vê o catálogo com
o Work e identifica corretamente o Hub. A configuração Hyprland do Work passa
na validação offline. A regressão completa passa 1011 testes, com 11 omissões
esperadas de hardware/condições externas; não existem units Host falhadas.

A primeira execução encontrou e fechou três incompatibilidades reais:

- o watchdog do Hub agora considera apenas processos da sua própria unit, sem
  confundir um compositor de validação ou de outro Environment;
- o launcher genérico transmite a política gráfica atual completa à sessão;
- o regresso aceita o cliente autenticado do Waybar ou do atalho Hyprland, em
  vez de exigir incorretamente um pai QuickShell.

O Work também exporta o ambiente Wayland para ativação D-Bus antes de iniciar
os restantes componentes, para os portais encontrarem o display correto.

## Isolamento e administração local

Dentro do Work, `/var/lib/apx` e `/root/.codex` do Host estão ocultos. O home é
privado e independente. O utilizador `apx` pertence a `wheel` e a política sudo
exige palavra-passe, mas a conta nova permanece bloqueada até o proprietário
fazer o enrollment seguro de uma palavra-passe local. Não foi copiada a
palavra-passe do Hub, não foi criada uma palavra-passe temporária e não foi
adicionado `NOPASSWD`.

Isto não impede o arranque direto do desktop nem o uso normal das aplicações.
Impede apenas operações administrativas via sudo até ao enrollment. O fluxo de
enrollment parado/primeiro-arranque continua a ser uma lacuna de produto a
resolver sem enfraquecer o isolamento.

## Uso normal

No Hub, clicar em **APX · HUB · ENVIRONMENTS**, escolher **Work** e confirmar a
troca. No Work, usar Rofi, Thunar, Firefox e Downloads; depois usar o botão da
barra para regressar normalmente ao Hub. Se os controlos falharem, `Super+E`
termina diretamente o compositor para o supervisor recuperar a sessão.

## Correção do retorno e prova repetida

Uma utilização posterior mostrou que a primeira prova não cobria uma falha do
cliente: o Host aceitava `return.to-hub`, mas esperava que o próprio cliente
executasse `hyprctl exit`. Quando isso não acontecia, Work só fechava pelo
failsafe de 120 segundos. O Host agora termina assincronamente a unit externa
exata depois da autenticação; o supervisor continua responsável por limpeza e
lançamento do Hub.

O lock do supervisor também é libertado por device/inode antes de o Hub ficar
disponível, permitindo outra troca imediata. O reconciliador de boot deixou de
estar fixo em `hub-ficticio` e cobre todos os registos gráficos v2 confiáveis.
O painel apresenta recusas e bloqueia cliques repetidos depois de aceitação.
Por escolha posterior do proprietário, `Super+E` é a saída de recuperação no
Hub e no Work, `Super+F` abre ficheiros e `Super+M` abre o menu sem executar transições.

A saída direta do Hub para tty1 foi observada fisicamente. No Work, duas provas
automatizadas foram antecipadas pelo uso normal do botão de retorno; por isso o
binding instalado e os testes estão confirmados, mas o toque físico
`Super+E` no Work continua pendente de observação e não é declarado provado.

Foram observados ciclos consecutivos completos, incluindo três repetições
adicionais às 07:29, 07:30 e 07:31. Depois do retorno das 07:01:20, o Hub ficou
saudável por mais de 23 minutos, incluindo todas as verificações periódicas do
watchdog. A saída final foi limpa: Hub e Work
`stopped`, nenhuma machine, nenhum estado gráfico ativo e nenhum lock. Detalhes,
segurança, rollback e diagnóstico estão em
`environment-switch-round-trip-hardening-v2-2026-08-12.md`.
