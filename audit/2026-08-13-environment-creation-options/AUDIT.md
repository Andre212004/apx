# Auditoria do fluxo de criação de Environments — 2026-08-13

## Âmbito e evidência

Fluxo observado no HUB físico ativo: abrir o catálogo de Environments e
comparar o que o formulário de criação comunica com as capacidades realmente
presentes no HUB e no `hyprland-base-v2`. Capturas desta execução:

1. `01-environment-list.png` — catálogo atual, saudável e legível.
2. `02-hub-control-centre.png` — Centro de Controlo atual, saudável e sem uma
   ação visual de Ficheiros no HUB.

O formulário “Novo Environment” não pôde ser aberto por IPC sem injetar input
físico ou alterar temporariamente o QML. Não se fez nenhuma dessas coisas numa
auditoria read-only. A sua estrutura foi confirmada no QML ativo: apenas nome,
descrição e criar.

## Passos

1. **Abrir Environments — saudável.** Identidade do HUB, estado e destinos são
   claros. A ação Criar existe, mas não antecipa que há escolhas adicionais.
2. **Compreender o que será criado — incompleto.** O formulário atual não diz
   se haverá GUI, rede, browser, ficheiros, sudo ou ferramentas básicas.
3. **Usar o HUB como referência — parcialmente saudável.** O Centro de
   Controlo expõe rede, Bluetooth, áudio, bloqueio e energia com boa hierarquia.
   O HUB tem Thunar e `Super+F` apesar de não mostrar “Ficheiros” neste painel.
4. **Receber um desktop quotidiano — incompleto.** A base v2 tem o núcleo do
   desktop, portais, Flatpak, ficheiros e ferramentas de compilação, mas não
   traz browser, aplicações de escritório/média, impressão/scanning, VPN,
   acessibilidade completa, backup ou restauro de sessão.

## Proposta de até 10 grupos

O modo-base fica acima dos toggles: **Desktop** (predefinido) ou **Terminal**.
Os grupos abaixo são capacidades concretas, não listas arbitrárias de pacotes.

1. **Desktop essencial** — Hyprland, QuickShell, terminal, notificações,
   clipboard, screenshots, lock/idle e portais. Ligado no modo Desktop;
   desligado e bloqueado no modo Terminal.
2. **Ficheiros e discos USB** — Thunar, GVFS/MTP/SMB, arquivos, UDisks e
   montagem assistida. Ligado por predefinição no Desktop.
3. **Internet e browser** — egress de rede, controlo Wi-Fi APX, DNS e Firefox.
   Ligado por predefinição no Desktop.
4. **Áudio e Bluetooth** — PipeWire/WirePlumber, microfone, áudio e controlo
   Bluetooth APX. Ligado por predefinição no Desktop.
5. **Aplicações e Flatpak** — Flatpak, Flathub, portais, Secret Service e uma
   superfície de descoberta/instalação. Ligado por predefinição no Desktop.
6. **Administração e ferramentas básicas** — sudo local, pacman, `less`, man,
   Git, `base-devel` e um artefacto `yay` revisto. Ligado por predefinição.
7. **Escritório e multimédia** — suite de escritório, PDF, imagens e vídeo.
   Desligado por predefinição.
8. **Dispositivos e periféricos** — webcam, comandos, impressão e scanner.
   Desligado; parte desta capacidade ainda precisa de mediação APX real.
9. **Idiomas e acessibilidade** — locale, fontes/emoji, teclado, leitor de ecrã,
   contraste e ampliação. Idioma/fontes ligados por predefinição; tecnologias
   assistivas ainda não certificadas.
10. **Continuidade e proteção de dados** — backup, restauro de sessão e
    recuperação. Desligado porque a implementação ainda não existe; deve ser
    rotulado como “em preparação”, não fingido como funcional.

## Predefinição recomendada

**Desktop quotidiano:** grupos 1–6 e a parte disponível do 9 ligados; 7, 8 e
10 desligados. **Terminal mínimo:** apenas 6, sem GUI, áudio, Bluetooth,
Flatpak ou dispositivos gráficos. Uma linha-resumo antes de Criar deve mostrar
o modo, número de grupos ativos, rede e estimativa de espaço.

## Credencial comum

O pedido de uma palavra-passe comum é claro, mas copiar o hash do HUB para
todos os Environments torna essa credencial diretamente portátil: root de um
workload pode ler o seu `/etc/shadow` e atacar a mesma credencial usada no HUB.
A recomendação é uma palavra-passe administrativa APX comum apenas aos
workloads, distinta da credencial do HUB. Se o proprietário mantiver a decisão
de usar exatamente a do HUB, isso deve ser registado como desvio de segurança
explícito antes da implementação.

## Limites

Capturas não provam navegação por teclado completa, leitor de ecrã, contraste
medido, hot-plug ou funcionamento físico dos periféricos. Pacotes presentes
também não equivalem a uma experiência certificada; os grupos 8–10 precisam de
backend antes de poderem ser toggles ativos.
