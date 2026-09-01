# Proposta: perfis de capacidade na criação de Environments — 2026-08-13

Estado: proposta auditada, ainda não implementada.

O formulário atual cria sempre `graphical-base` de `hyprland-base-v2` e aceita
apenas nome e descrição. A proposta introduz uma escolha de modo-base
**Desktop** ou **Terminal**, seguida por no máximo dez grupos de capacidade.
A lista, predefinições, evidência e limites estão em
`audit/2026-08-13-environment-creation-options/AUDIT.md`.

Os grupos propostos são: Desktop essencial; Ficheiros e discos USB; Internet e
browser; Áudio e Bluetooth; Aplicações e Flatpak; Administração e ferramentas
básicas; Escritório e multimédia; Dispositivos e periféricos; Idiomas e
acessibilidade; Continuidade e proteção de dados.

O perfil quotidiano liga por predefinição os seis primeiros e a parte já
disponível de idiomas/fontes. O perfil Terminal liga apenas Administração e
ferramentas básicas. Capacidades ainda inexistentes não podem ser apresentadas
como toggles funcionais: aparecem desativadas como “em preparação” ou ficam
fora da primeira versão.

`yay` não pertence aos repositórios oficiais Arch. Incluí-lo exige um artefacto
APX revisto e versionado ou uma instalação AUR explícita; não se deve executar
um build arbitrário como root durante a criação.

O pedido de usar a mesma palavra-passe do HUB em todos os Environments altera a
separação de credenciais confirmada até aqui. Copiar o mesmo hash permitiria a
root de qualquer workload extrair o verificador usado pelo HUB. A alternativa
recomendada é uma credencial administrativa comum apenas aos workloads,
distinta do HUB. Nenhuma credencial deve atravessar argumentos, logs, QML
persistente ou documentação.

No HUB atual não existe um botão “Ficheiros” no Centro de Controlo, mas Thunar
está instalado e `Super+F` abre-o. Interpretar “apagar o coiso de ficheiros”
como remover Thunar e o atalho requer confirmação antes de desinstalar o pacote
ou alterar o binding.
