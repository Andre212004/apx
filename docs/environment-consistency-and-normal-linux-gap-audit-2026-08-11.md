# Auditoria de consistência dos Environments vs. Linux normal

Data: 11 de agosto de 2026
Alvo observado: `apx-hub` físico, 1920×1080 a 150%

## Atualização depois da implementação

Os bloqueios P0 descritos abaixo eram o estado observado no início da auditoria
e já não representam o estado instalado no fim do trabalho:

- a contabilidade Btrfs está consistente; o HUB tem limites root/home de
  16/32 GiB e novas criações protegem uma reserva de 96 GiB para o Host;
- o arranque certificado da base v2 tem `systemd-logind`, D-Bus,
  `systemd --user` e o bus do utilizador funcionais;
- `hyprland-base-v2` é uma raiz imutável de 540 pacotes com chaveiro pacman,
  locales, ferramentas de compilação, `clear`, `less`, gestor de ficheiros,
  notificações, porta-chaves, portais, UDisks, Flatpak/Flathub, rede e limpeza
  periódica de cache;
- tarefas pesadas ficam dentro de 600% CPU, 10/12 GiB de memória e 4096 tarefas,
  com peso de CPU/I/O do Environment e prioridade inferior para shells batch;
- criador, catálogo, launcher genérico e troca aceitam todos a mesma release e
  config seed v2; a regressão completa passa 1004 testes, 11 saltados.

A tentativa física a 100% tornou a Central demasiado pequena. O estado live
atual usa `controlCenterScale: 1`, isto é, a escala nativa do desktop a 150%, e
os SVG entram diretamente por `ToolButton.icon`, sem `MultiEffect`. A nitidez
percebida deve ser revista pelo proprietário depois de desbloquear a sessão.

Continuam deliberadamente não certificados: emparelhar/usar um periférico
Bluetooth real, hot-plug genérico de USB/câmara/impressão/monitor, continuidade
em segundo plano e restauro de janelas, transferência de ficheiros entre
Environments, backup e acessibilidade. A interface de criação no botão
Environments é o próximo passo; a fundação v2 já não deve ser substituída por
uma cópia do HUB vivo.

## Veredito

O HUB já consegue executar aplicações Linux reais — incluindo Brave com GPU,
áudio, rede e sandbox de utilizador — mas ainda não tem a fundação completa de
uma sessão Linux de uso diário. Antes de multiplicar Environments, há quatro
bloqueios principais: armazenamento sem limites fiáveis, serviços normais de
sessão ausentes, atualizações/caches repetidas por Environment e recursos do
desktop ainda misturados com tarefas pesadas.

A separação do Host está a funcionar e deve ser mantida. O problema é que cada
Environment ainda precisa de receber uma base coerente de “computador normal”,
em vez de se ir completando manualmente depois da criação.

## Central de Controlo

### Evidência atual

- `01-control-centre-100-before.png`: 100% físico. Ocupa pouco espaço, mas texto,
  ícones e alvos ficam pequenos neste painel.
- `02-control-centre-125-direct-icons.png`: 125% físico. Recupera legibilidade e
  mantém a área total claramente abaixo da versão original a 150%.
- `03-bluetooth-expanded-125.png`: painel Bluetooth expandido a 125%, sem corte
  ou overflow visível.

O aspeto pixelizado vinha de duas reduções: a Central inteira era transformada
para 2/3 e cada SVG passava antes por uma textura escondida mais um
`MultiEffect` de recoloração. O novo estado usa 125% físico (`5/6` dentro do
desktop a 150%) e o pipeline nativo `ToolButton.icon` do Qt. Os SVG Adwaita
continuam a ser os ativos reais; não foram redesenhados ou convertidos para
bitmaps.

O resultado digital é mais limpo. A confirmação final da nitidez depende ainda
da observação física do proprietário. Texto secundário e botões de 40 px físicos
continuam abaixo de um alvo conservador de acessibilidade; isto é aceitável para
rato no piloto, mas deve ser configurável antes de declarar acessibilidade.

## Percurso de uso e estado

1. **Entrar no Environment — parcial.** O desktop abre, mas `systemd-logind`
   está falhado e não existe um gestor `systemd --user`. Num desktop normal,
   ambos sustentam sessões, autostart, timers, inibição de suspensão e vários
   serviços de aplicações.
2. **Instalar e atualizar aplicações — parcial.** `sudo`, `pacman`, AUR e Brave
   funcionam. Contudo, cada Environment mantém bases de dados e caches próprios;
   uma base desatualizada já produziu um 404 de assinatura. Um Linux normal tem
   normalmente uma única linha de atualização visível ao utilizador.
3. **Usar aplicações comuns — parcial.** Brave abre com Wayland e GPU e tornou-se
   o browser predefinido. Faltam gestor de ficheiros, daemon de notificações,
   porta-chaves ativo e uma pilha de aplicações essenciais definida pela base.
4. **Guardar dados e instalar muito software — em risco.** Os subvolumes root e
   home do HUB não têm limite; o estado Btrfs está marcado como inconsistente e
   a própria sessão mostra os 476 GB do Host. Um Environment pode crescer até
   afetar todos os outros.
5. **Executar tarefas pesadas — parcial.** O limite externo de 200% CPU e 4 GB
   de RAM existe. Porém, desktop e compilação partilham o mesmo domínio de CPU.
   Os terminais foram rebaixados, mas tarefas iniciadas por outras aplicações
   ainda podem provocar lentidão.
6. **Ligar dispositivos — incompleto.** Os dispositivos internos previstos
   funcionam. USB genérico, webcam, impressão, scanning, áudio Bluetooth,
   periféricos Bluetooth reais e hot-plug ainda não são uma promessa segura.
7. **Mudar e regressar ao Environment — incompleto.** A troca termina a sessão;
   tarefas em segundo plano param e janelas não são restauradas. Num computador
   normal, downloads, sincronização e sessão continuam normalmente ativos.
8. **Recuperar de erro ou perda — parcial.** Existem snapshots e atualização
   coordenada, mas não existe ainda backup de dados pessoais, restauro de sessão
   ou uma experiência final de espaço/quotas/rollback para o utilizador.

## Problemas futuros mais prováveis

### P0 — resolver antes de criar Environments para uso real

#### 1. Um Environment pode consumir o armazenamento comum

Evidência atual:

- root do HUB: 2,45 GiB referenciados, sem limite;
- home do HUB: 1,08 GiB referenciados, sem limite;
- Btrfs: `Inconsistent: yes (rescan needed)`;
- `/var/lib/apx`: cerca de 35 GB contabilizados por `du`, incluindo snapshots e
  dados partilhados/referenciados;
- o utilizador vê 476 GB disponíveis, não uma capacidade do Environment.

Antes de criar novos Environments é obrigatório recuperar a contabilidade,
aplicar limites root/home, reservar espaço mínimo para o Host e mostrar na UI
“usado / limite / espaço do Host reservado”. Enquanto a contabilidade estiver
inconsistente, não se deve fingir que uma quota está aplicada.

#### 2. Falta uma sessão Linux completa

`systemd-logind` está falhado, `user@1000.service` está inativo e não existe bus
do gestor de utilizador. Isto pode quebrar silenciosamente:

- autostart e serviços `systemd --user`;
- timers de sincronização e agentes de credenciais;
- inibição de suspensão durante downloads ou chamadas;
- aplicações que consultam `org.freedesktop.login1`;
- serviços instalados por aplicações que esperam uma sessão desktop normal.

O launcher deve criar uma sessão reconhecida e um gestor de utilizador funcional
sem lhes dar autoridade sobre o Host.

#### 3. A imagem-base ainda é acidental

O HUB começou sem browser, gestor de ficheiros, `less` ou AUR helper; esses
componentes foram acrescentados manualmente. A base seguinte precisa de um
manifesto versionado com, no mínimo:

- browser e gestor de ficheiros;
- terminal e ferramentas básicas (`less`, editor, arquivador);
- notificações;
- porta-chaves/Secret Service;
- portais e respetivos backends ativos;
- áudio, clipboard, MIME/default apps e launcher;
- locale escolhido e gerado;
- política explícita para AUR e Flatpak.

Não se deve clonar o HUB vivo. Deve-se construir uma base comum imutável e
aplicar por cima apenas o papel visual/funcional de cada Environment.

#### 4. Atualizações multiplicam-se

Cada Environment possui pacman, keyring, bases e cache. Com dez Environments há
dez sistemas Arch para manter, dez caches e dez oportunidades de ficar
desatualizado. O modo `follow-host` existe, mas deve tornar-se explícito em toda
nova registration e a Central deve mostrar claramente “atualizado”, “excluído”
ou “bloqueado”. Atualizações manuais dentro do Environment não podem deixar o
catálogo central a acreditar que outro estado está instalado.

### P1 — necessário para parecer um computador diário

#### 5. Notificações, segredos e portais estão incompletos

Existe `xdg-desktop-portal` e descrição dos backends GTK/Hyprland, mas não há
daemon de notificações, gestor de chaves em execução nem teste final de file
chooser, screen sharing e notificações do browser. `secret-tool` existir não
significa que exista um Secret Service funcional.

Sem esta camada, logins podem não ficar guardados como esperado, chamadas podem
falhar ao partilhar o ecrã e aplicações podem “funcionar” sem apresentar pedidos
ou avisos importantes.

#### 6. Hardware é estático

O launcher entrega dispositivos exatos no arranque. Num Linux normal, ligar um
rato, pen USB, webcam, monitor ou auscultadores depois do login costuma bastar.
No APX é necessário um broker revogável de hot-plug, com escolha do Environment
destino e feedback quando um dispositivo foi recusado ou está ocupado noutro.

#### 7. Não existe continuidade em segundo plano

Mudar de Environment encerra o atual. Isso protege isolamento, mas também para
downloads, chamadas, sincronização, builds e media. Precisamos de três políticas
com nomes claros:

- **Parar ao sair** — máxima separação;
- **Manter tarefas aprovadas** — serviços específicos continuam sem desktop;
- **Guardar e restaurar sessão** — relança aplicações suportadas.

O utilizador não deve descobrir esta diferença ao perder um download.

#### 8. Prioridade de recursos ainda é um remendo

Baixar a prioridade do Bash protege a interface durante `yay`, mas não cobre
IDE, browser, jogos, compiladores iniciados por GUI ou serviços. A solução final
é separar compositor/shell, aplicações interativas e trabalho batch em
sub-cgroups com pesos e limites próprios, além de mostrar CPU/RAM/disco na
Central.

### P2 — consistência, acessibilidade e recuperação

#### 9. Locale está selecionado mas não gerado

O Environment anuncia `en_US.UTF-8`, mas `locale` informa que não consegue
carregá-lo. Isto pode produzir avisos, ordenação/texto inconsistentes e aplicações
em inglês. A criação deve escolher e gerar locale, idioma, teclado, fuso horário
e formatos regionais como um único perfil.

#### 10. Faltam defaults e migrações de configuração

Configurações hoje são copiadas e depois alteradas no home. Quando a base melhora,
um Environment antigo pode continuar com QML, atalhos ou configurações
obsoletas. Cada componente precisa de versão, migração segura e distinção entre
“default APX” e “personalização do utilizador”.

#### 11. Acessibilidade ainda não está certificada

As capturas confirmam contraste visual razoável e ausência de corte, mas não
provam navegação completa por teclado, ordem de foco, leitor de ecrã, nomes
acessíveis, zoom ou redução de movimento. A escala da Central deve tornar-se uma
preferência comum (100/125/150), sendo 125 o default recomendado neste painel.

#### 12. Dados entre Environments precisam de uma história explícita

A ausência de partilha automática é uma proteção, mas um utilizador normal
espera conseguir abrir um documento noutro contexto. Será necessário um fluxo
deliberado de exportar/importar ou uma pasta de troca mediada, com origem,
destino e confirmação claros — nunca mounts cruzados invisíveis.

## O que é diferença intencional, não defeito

- `root` dentro do Environment não é root do Host.
- Dispositivos e serviços do Host não aparecem só porque uma aplicação os pede.
- Aplicações AUR têm poder sobre todo o home daquele Environment; o isolamento
  protege os outros Environments, não os dados dentro do mesmo.
- Parar um Environment remove os seus processos e serviços.
- Não existe partilha automática de ficheiros, credenciais ou notificações.

Estas diferenças devem aparecer no onboarding e nas confirmações; escondê-las
faria o APX parecer avariado quando está a aplicar a sua política.

## Ordem recomendada

1. Recuperar e impor quotas Btrfs antes de permitir criação generalizada.
2. Criar uma sessão completa com logind, `systemd --user`, notificações, segredos
   e portais testados.
3. Publicar uma base comum versionada e uma matriz de testes de aplicações.
4. Separar recursos de UI/interativo/batch por cgroups.
5. Implementar hot-plug e os perfis de hardware.
6. Fechar atualização coordenada, cache e estado de versões.
7. Implementar políticas de background/restauro e transferência mediada.
8. Só então promover o botão Environments de catálogo para criação diária.

## Limites da evidência

As capturas desta execução provam layout, tamanho, ausência de corte e melhoria
digital dos ícones. Não provam a perceção física no painel, acessibilidade por
tecnologia assistiva, ligação Bluetooth real, screen sharing do Brave, webcam,
USB, impressão ou restauração após falha. Esses itens continuam “não
certificados”, não “definitivamente avariados”.
