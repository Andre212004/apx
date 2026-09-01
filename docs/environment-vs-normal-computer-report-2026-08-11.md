# Relatório: Environment APX vs. computador normal

Data da avaliação: 11 de agosto de 2026
Environment observado: `apx-hub`, no hardware físico do piloto

## Resumo em linguagem simples

O HUB já é um ambiente gráfico Linux real e isolado. Tem janelas, terminal, Internet, som, microfone, teclado, touchpad, área de transferência, capturas de ecrã e instalação de pacotes Arch. O utilizador `apx` pertence ao grupo administrativo e pode usar `sudo` dentro do HUB.

Ainda não é, porém, um substituto completo de um computador normal. O que falta não é principalmente “mais isolamento”; é a camada quotidiana que normalmente damos por garantida: navegador e gestor de ficheiros pré-instalados, loja gráfica de aplicações, suporte simples a discos USB, webcam, impressoras, VPN, ligação Bluetooth comprovada de ponta a ponta, dispositivos ligados depois do arranque, vários monitores e restauro da sessão.

Há ainda uma distinção importante: ter administração total **dentro** do Environment não significa ter administração do Host. O `root` do HUB é todo-poderoso dentro do HUB, mas é deliberadamente um utilizador sem privilégios no Host. Isto é o que permite instalar livremente sem que uma aplicação do Environment consiga destruir ou reconfigurar o sistema base.

## O que já funciona como num computador normal

| Área | Estado atual | Em termos práticos |
|---|---|---|
| Ambiente gráfico | Funciona | Hyprland, barra, launcher e janelas funcionam no ecrã interno. |
| Terminal Linux | Funciona | É uma shell Linux normal; `TERM=xterm-256color` já foi corrigido para `clear` e aplicações de terminal. A correção entra plenamente no próximo arranque da sessão. |
| Administração local | Funciona | `apx` está em `wheel`, tem palavra-passe e a política permite `(ALL:ALL) ALL`. `sudo` pede a palavra-passe local, como num Arch normal. |
| Pacotes Arch | Funciona | `pacman` instala pacotes dos repositórios oficiais dentro do Environment. As alterações ficam nesse Environment. |
| Internet | Funciona | O Environment tem rede privada e sai para a Internet através do Host, sem receber as credenciais Wi-Fi do Host. |
| Som e microfone | Funciona | PipeWire/WirePlumber existem e o HUB recebe os dispositivos autorizados. |
| Teclado, touchpad e rato interno | Funciona | Os dispositivos físicos previstos são entregues ao HUB no arranque. |
| Área de transferência e capturas | Funciona | `wl-copy`, `wl-paste`, `grim`, `slurp` e os portais Wayland estão presentes. |
| Wi-Fi e energia | Funciona pelo HUB | A Central pede ao Host para executar operações autorizadas; não recebe acesso direto e indiscriminado ao hardware. |
| Separação entre ambientes | Funciona | Ficheiros, pacotes, processos e administração ficam separados por Environment. |

## O que funciona, mas ainda não parece um computador normal

| Área | Limitação atual | Impacto para a pessoa |
|---|---|---|
| Instalar aplicações | Não há Flatpak, loja gráfica ou helper AUR pré-instalado. `git`, `base-devel` e `makepkg` permitem o processo AUR manual. O Brave não está no repositório oficial do Arch. | `sudo pacman -S brave` não é um teste válido de `sudo`: mesmo com permissões, o pacote não existe nesse repositório. É preciso AUR, Flatpak ou outra fonte. |
| Aplicações básicas | No HUB observado não há navegador nem gestor de ficheiros gráfico instalados. | O desktop abre, mas começa demasiado “vazio” para uso comum. |
| Palavra-passe administrativa | `sudo` exige a palavra-passe local do utilizador `apx`. | Se a palavra-passe inicial não for claramente apresentada/definida no onboarding, parece que o utilizador “não tem permissões”. |
| Bluetooth | Estado, scan e pedidos de ligação existem; um scan real anterior encontrou dispositivos. A ligação completa a periférico real ainda não está certificada. | Ainda não devemos prometer que auscultadores, rato e teclado Bluetooth funcionarão sempre. |
| Dispositivos ligados depois | Os dispositivos são atribuídos no arranque com uma lista concreta. Hot-plug geral ainda não está resolvido. | Um rato USB ligado depois de iniciar o Environment pode não aparecer automaticamente. |
| Notificações | O protocolo/base gráfica existe, mas não há uma experiência de notificações de desktop completa validada. | Aplicações podem não apresentar e organizar avisos como num desktop comum. |
| Sessão | A identidade do Environment persiste, mas o restauro de janelas e aplicações ainda não está implementado. | Ao voltar ao Environment, não se recupera automaticamente o “computador como estava”. |
| Trabalho em segundo plano | Serviços do Environment dependem do seu estado ativo. | Downloads, sincronizações ou tarefas longas não têm ainda a mesma garantia de um computador sempre ligado. |
| Ecrãs | O piloto está afinado para o ecrã interno exato. | Monitor externo, múltiplos monitores e mudanças dinâmicas ainda não são uma promessa do produto. |
| Central de Controlo | As ações fundamentais existem, mas algumas têm atraso visível e os ícones parecem suaves no painel físico. | A sensação de resposta e acabamento ainda fica abaixo de um desktop maduro. |

## O que ainda não está disponível ou certificado

- Discos USB e armazenamento removível com montagem segura e interface simples.
- Webcam/câmara.
- Impressoras e scanners.
- VPN de utilização comum.
- Hibernação.
- Bluetooth de ponta a ponta certificado, incluindo áudio Bluetooth e periféricos HID.
- Gestão geral de dispositivos hot-plug.
- Restauro da sessão e das aplicações.
- Loja gráfica de aplicações e um caminho suportado para Flatpak/AUR.
- Partilha de ficheiros entre Environments. Esta ausência é, por agora, uma decisão de isolamento e não apenas um bug.
- Criação, dimensionamento, eliminação e recuperação de Environments numa interface final para utilizadores.

## Percurso atual e “saúde” da experiência

1. **Ligar o computador e chegar ao HUB — saudável, com uma ressalva.** O desktop abre e o terminal automático foi removido do launcher, mas a sessão atualmente aberta ainda mostra a janela antiga; a alteração completa exige reiniciar a sessão/máquina.
2. **Usar janelas, terminal, rede e áudio — saudável.** A fundação técnica está funcional.
3. **Instalar uma aplicação — parcialmente saudável.** `sudo` e `pacman` funcionam, mas faltam descoberta de aplicações, feedback claro sobre fontes e suporte conveniente para aplicações fora dos repositórios oficiais.
4. **Usar periféricos — incompleto.** Os dispositivos internos previstos funcionam; Bluetooth real, USB removível, câmara, impressão e hot-plug ainda não têm cobertura suficiente.
5. **Suspender, bloquear e desligar — razoavelmente saudável no HUB.** As operações passam pelos serviços autorizados do Host; hibernação não existe.
6. **Sair e voltar ao trabalho — incompleto.** O Environment continua a existir, mas a sessão de trabalho não é restaurada como estava.
7. **Criar outro Environment — ainda não pronto para utilizador final.** A arquitetura e o catálogo existem, mas falta fechar o modelo de base, permissões, hardware, aplicações iniciais e a interface de criação.

## Central de Controlo e ícones

Os ficheiros-fonte não eram imagens de baixa resolução. O problema foi isolado ao caminho de renderização: os SVG eram rasterizados, recoloridos por `MultiEffect` e depois a Central inteira era reduzida. O estado atual usa 125% físico e o pipeline nativo de ícones do Qt, sem esse efeito intermédio. A captura digital está mais limpa; a nitidez física final continua dependente da observação do proprietário. O botão da barra ainda aparece como texto (`[I]`/`[A]`) e deve ser substituído por um ícone real.

Recomendação: **manter a Central APX**, mas corrigir o acabamento. Ela contém ações específicas do produto — Host, Environments, snapshots, atualizações e políticas de dispositivos — que os painéis Linux existentes não compreendem. O próximo ensaio deve:

1. renderizar ícones simbólicos diretamente, sem recoloração por efeito em tempo real;
2. usar ativos SVG reais e consistentes, através de `IconImage`/tema de ícones;
3. alinhar tamanhos físicos (por exemplo 16/20/24 px lógicos) à escala 150%;
4. substituir os símbolos de texto da barra por ativos reais;
5. medir separadamente o tempo de clique, pedido ao serviço e atualização visual, para localizar o atraso.

Substituir tudo por um componente existente teria custos relevantes:

- **SwayNotificationCenter** é uma boa opção para notificações, calendário, media, volume e botões, mas as ações personalizadas são comandos de shell e teriam de ser adaptadas cuidadosamente aos clientes autenticados APX.
- **nwg-panel** oferece uma barra e controlos convencionais, mas mudaria a identidade visual e não cobre a gestão específica de Environments.
- **Waybar** já está disponível e é uma boa base para barras de Environments comuns, mas não substitui uma Central de Controlo rica.

Assim, a melhor divisão é: uma base visual comum e simples para todos os Environments, e uma camada de gestão APX adicional apenas no HUB.

## O que deve ficar resolvido antes de criar novos Environments

### Prioridade 0 — definir a base correta

1. Criar uma **imagem-base comum**, revista e versionada, com desktop, ficheiros, navegador, terminal, notificações, áudio, portais e onboarding de `sudo`.
2. Não clonar o HUB em execução. “Baseado no HUB” deve significar herdar a estética e a base comum, nunca as permissões de gestão, credenciais, estado ou ferramentas exclusivas do HUB.
3. Definir perfis claros de hardware: ecrã, áudio, microfone, câmara, USB, Bluetooth e hot-plug.
4. Definir o ciclo de vida: o que continua a correr quando se muda de Environment e o que é restaurado quando se regressa.

### Prioridade 1 — fechar a experiência de computador diário

1. Instalação de aplicações: repositório oficial + decisão explícita sobre Flatpak e/ou AUR.
2. Gestor de ficheiros, navegador, notificações e gestão de credenciais.
3. Bluetooth real, armazenamento USB, monitor externo e VPN.
4. Mensagens claras para permissões, palavras-passe, falhas e operações demoradas.
5. Medição e correção da latência da Central de Controlo.

### Prioridade 2 — depois da primeira geração de Environments

1. Impressão/scanning, webcam avançada e hibernação.
2. Restauro mais sofisticado por aplicação.
3. Loja de aplicações e gestão gráfica de armazenamento/quotas.

## Decisão recomendada

Ainda não devemos gerar novos Environments clonando o HUB atual. Devemos primeiro extrair dele uma **base comum de desktop**, retirar tudo o que é exclusivo de gestão e fechar os itens de Prioridade 0. Depois disso, o botão “Environments” pode criar perfis em cima dessa base: por exemplo Trabalho, Desenvolvimento, Privado ou Gaming, cada um com aplicações, recursos e dispositivos próprios.

Não é necessário esperar por impressoras, hibernação ou restauro perfeito para começar um primeiro protótipo. É necessário, sim, garantir que a base não propaga privilégios do HUB, que a administração local é compreensível e que hardware/aplicações/ciclo de vida têm regras previsíveis.

## Evidência e limites desta avaliação

Esta avaliação combina inspeção do `apx-hub` em execução, configuração e testes do projeto, documentação técnica existente e capturas do ecrã físico nesta sessão. Foi confirmado diretamente que o utilizador `apx` tem `sudo`, que `pacman` está disponível, que os portais Wayland existem e que navegador, gestor de ficheiros, Flatpak, impressão, scanning e VPN não estão instalados na imagem observada.

Não foi efetuada nesta avaliação uma ligação real a cada tipo de periférico, nem uma medição instrumental completa da latência clique-a-clique. Esses pontos estão descritos como “não certificados” ou “a medir”, e não como falhas definitivamente provadas.

Referências de alternativas: [SwayNotificationCenter](https://github.com/ErikReider/SwayNotificationCenter), [nwg-panel](https://nwg-piotr.github.io/nwg-shell/nwg-panel.html), [Waybar](https://github.com/Alexays/Waybar), [Quickshell IconImage](https://quickshell.org/docs/v0.2.1/types/Quickshell.Widgets/IconImage/), [Qt MultiEffect](https://doc.qt.io/qt-6/qml-qtquick-effects-multieffect.html), [Qt High DPI](https://doc.qt.io/qt-6.10/highdpi.html).
