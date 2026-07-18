# APX Physical Pilot State and Cleanup Audit v1

**Sessão:** recolha de evidências, somente leitura  
**Data da evidência:** 2026-07-17  
**Estado:** concluída com observações pendentes; nenhuma limpeza autorizada

A verificação final mostra:

- runtime APX disponível;
- estado em `/var/lib/apx`, filesystem Btrfs;
- host saudável;
- `development` em execução;
- `hub` em execução;
- nenhum estado APX incerto visível na saída final.

Os identificadores completos de geração mostrados na fotografia não estão suficientemente legíveis para transcrição segura, por isso não são reproduzidos.

## 1. Resultado executivo

A identidade física e o contexto correspondem ao piloto esperado:

| Campo | Evidência observada |
|---|---|
| Utilizador do host | `root` |
| Hostname | `apx-host` |
| Virtualização | `none` |
| Fabricante | `LENOVO` |
| Produto | `82JU` |
| Board | `LNVNB161216` |
| Marcador do piloto | `profile=apx-physical-headless-pilot-v1` |
| Armazenamento APX | Btrfs em `/dev/mapper/cryptroot[/@apx]` |
| Environments | `hub` e `development` |
| Estado final APX | host saudável; ambos os Environments em execução |
| Unidades falhadas no host | nenhuma |
| Quotas Btrfs | ativadas, full accounting, não inconsistentes |

A auditoria evidencia que:

- as Fases 1–8 estão materialmente refletidas no estado observado;
- a Fase 9 está **parcialmente evidenciada e deliberadamente incompleta**;
- a Fase 10 permanece **bloqueada**;
- nenhuma eliminação, remoção de pacote ou alteração de serviço é autorizada.

## 2. Classificação obrigatória

### Expected and required — esperado e necessário

| Objeto | Localização | Proprietário | Finalidade | Evidência |
|---|---|---:|---|---|
| Marcador físico APX | `/etc/apx-physical-pilot` | root | Identificar o piloto físico autorizado | Perfil observado como `apx-physical-headless-pilot-v1` |
| Estado APX | `/var/lib/apx` | root | Estado persistente do runtime APX | 7,0 GiB; Btrfs; mount `@apx`; estrutura esperada |
| Environment Hub | `/var/lib/apx/environments/hub` | root | Ambiente mínimo de controlo/Hub | Registo `name=hub`, `role=hub`, release `hub-headless-v3`, estado `running` |
| Environment Development | `/var/lib/apx/environments/development` | root | Ambiente de desenvolvimento isolado | Registo `name=development`, `role=development`, release `development-headless-v1`, estado `running` |
| Release ativa do Hub | `/var/lib/apx/releases/hub-headless-v3` | root | Base do Hub atual | Corresponde ao registo do Hub |
| Release ativa do Development | `/var/lib/apx/releases/development-headless-v1` | root | Base do Development atual | Corresponde ao registo do Development |
| Outras releases APX | `hub-headless-v1`, `minimal-headless-v1` | root | Proveniência, recuperação ou dependências de release | Presentes; não há prova de que sejam dispensáveis |
| Planos APX | `/var/lib/apx/plans/*.json` | root, modo 600 | Planos operacionais/recovery | Dois ficheiros pequenos observados |
| Journal APX | `/var/lib/apx/journal/operations.jsonl` | root | Registo de operações | Cerca de 9142 bytes; conteúdo não exibido |
| Qgroups Btrfs | filesystem APX | sistema | Accounting e limites | Quotas enabled; `Inconsistent: no`; 31 qgroups |
| Repositório Development | `/home/apx/work/apx` | `apx:apx` | Fonte de trabalho e cópia GitHub | Único clone no Development; 29 MiB; branch `master`; working tree limpo |
| Remoto GitHub | `origin` | `apx` | Cópia remota da fonte | Fetch/push em `https://github.com/Andre212004/apx.git` |
| Autenticação GitHub | `/home/apx/.config/gh/hosts.yml` | `apx` | Acesso GitHub do Development | `gh auth status` autenticado; token mascarado |
| Codex ativo | release `0.114.5-…-linux-musl` | `apx:apx` | Ferramenta de desenvolvimento | `command -v` resolve para a release 0.114.5; login via ChatGPT |
| Pacotes de desenvolvimento | Development | sistema | Toolchain e operação | `base-devel`, `git`, `github-cli`, `nodejs`, `npm`, `python`, `qwen-code`, `ollama` |
| Qwen Code | Development | sistema | Ferramenta prevista na fase de desenvolvimento | `qwen-code 0.19.2-1` |
| Ollama package | Development | sistema | Runtime local, sem modelo | `ollama 0.32.0-1` |
| Conta Ollama | `ollama`, UID/GID `968:968` | sistema | Executar o serviço isoladamente | Home `/var/lib/ollama`, shell `nologin` |
| Unidade Ollama | `/usr/lib/systemd/system/ollama.service` | root | Executar `ollama serve` | `enabled`, `active`, utilizador/grupo `ollama` |
| Listener Ollama | `127.0.0.1:11434` dentro do Development | processo Ollama | API somente loopback | Nenhum bind externo observado |
| Hub mínimo | Environment `apx-hub` | root | Papel limitado do Hub | Pacotes explícitos apenas `base`, `python`, `systemd` |
| Serviços base | Host/Hub/Development | sistema | Operação normal | Apenas serviços base, e Ollama adicional no Development |
| Journals do host | journal do sistema | root | Diagnóstico e proveniência | 8 MiB |
| Cache do host | `/var/cache` | root | Cache de pacotes/sistema | 708 MiB; preservado |
| Diretórios temporários systemd | `/tmp`, `/var/tmp` | sistema | Estado transitório normal | `systemd-private-*`, sockets X/ICE e `nspawn-root-*` |

### Expected temporary — esperado temporário

| Objeto | Porque é temporário | Pré-requisito antes da remoção |
|---|---|---|
| `/root/apx-bootstrap` | Clone de bootstrap previsto no handoff; 20 MiB | Confirmar que recuperação, instalação, atualização e fonte no GitHub já não dependem dele; aprovação explícita da lista exata |
| Pacote `git` no host | Foi instalado explicitamente e o host steady-state deve ser mínimo | Confirmar que nenhum fluxo de recuperação, bootstrap, atualização ou diagnóstico do host depende de Git |
| Eventual material transitório em `/var/cache` | Pode conter cache de pacotes acumulado | Definir política explícita de retenção, rollback e recuperação; não assumir que 708 MiB são lixo |
| Serviço/processo Ollama em execução | A instalação package-only foi efetuada; o modelo foi deliberadamente adiado | A Fase 9 deve decidir se o serviço fica enabled/active sem modelos ou se o teardown é parte da configuração aprovada |

`/root/apx-bootstrap-recovery` **não** é colocado nesta tabela. Embora semelhante ao clone de bootstrap, o nome e o conteúdo aparente sugerem função de recuperação e não há autorização inicial para o remover.

### Unexpected review candidate — candidato inesperado para revisão

| Objeto | Factos observados | Origem possível | Consequência da remoção | Evidência em falta |
|---|---|---|---|---|
| `/root/apx-bootstrap-recovery` | Clone Git separado, 21 MiB, com documentação, scripts, testes e `RECOVERY_PROJECT_STATE.md` | Cópia deliberada para recuperação | Pode eliminar a única via local de recuperação ou contexto operacional | Relação com o repositório principal, estado remoto, commit exato, documentação que o referencia |
| Codex release `0.114.4-…-linux-musl` | Binário de cerca de 299 MB; release 0.114.5 é a ativa | Release anterior mantida pelo mecanismo de atualização do Codex | Pode impedir rollback ou quebrar convenções internas do updater | Política oficial/local de retenção, rollback testado, confirmação de que auth/config não dependem dela |
| Cache/estado Codex total de 831 MiB | `.codex` representa a maioria dos 1019 MiB de `/home/apx` | Releases, cache e estado operacional do Codex | Pode apagar login, configuração, histórico operacional ou binário ativo | Inventário interno apenas por metadata, distinção entre credenciais, cache, releases e estado necessário |
| Releases APX antigas `hub-headless-v1` e `minimal-headless-v1` | Presentes em `releases`, não são as releases registadas atuais | Bootstrap, rollback, proveniência ou base herdada | Pode quebrar rollback, recuperação ou criação futura de Environment | Referências em planos, manifests, journal, scripts de recuperação e política de releases |
| Dois ficheiros em `/var/lib/apx/plans` | Planos JSON de modo 600, conteúdo não inspecionado | Operações concluídas ou pendentes | Remoção pode perder rollback, auditoria ou operação ainda relevante | Estado semântico de cada plano e ligação ao journal |
| `/var/cache` com 708 MiB | Maior objeto transitório observado no host | Principalmente cache de pacotes, possivelmente outros caches | Pode reduzir capacidade de reinstalação/rollback offline | Distribuição por subdiretório e política de retenção |
| Serviço Ollama enabled/active sem modelos | Listener loopback ativo e diretório de modelos não criado | Instalação package-only conforme reportada | Desativar/remover mudaria a configuração da Fase 9 e pode inviabilizar testes futuros | Decisão de design para serviço persistente, teardown e modelo externo |
| `/usr/share/ollama` | Diretório vazio, 4 KiB | Estrutura criada pelo pacote | Remoção manual criaria divergência do pacote | Confirmação via lista de ficheiros do pacote, se alguma limpeza futura o considerar |

### Preserve or unknown — preservar ou desconhecido

| Objeto | Incerteza | Evidência necessária |
|---|---|---|
| `/root/apx-bootstrap-recovery` | Valor de recuperação potencialmente crítico | Commit, remoto, referências em documentação e teste de recuperação |
| Releases APX não ativas | Podem ser necessárias para rollback/proveniência | Dependências nos manifests, plans, journal e scripts |
| Planos e journal APX | Conteúdo não foi analisado nesta sessão | Revisão controlada em Development, sem exposição de segredos |
| Todos os 31 qgroups | Só o qgroup `0/261` ficou visível através de `/var/lib/apx` | Saída do procedimento v3 de recuperação de quotas, executado pelo script revisto |
| Limites Development 16/8 GiB | Não ficaram visíveis nesta montagem | Evidência produzida pelo fluxo de quota recovery v3 |
| Inacessibilidade ativa host/Hub → Ollama | Listener é apenas loopback, mas `machinectl ... Address` não devolveu endereço | Teste previsto no repositório que não altere rede nem lifecycle |
| Conteúdo detalhado de `.codex` | Pode incluir credenciais e estado necessário | Inventário sanitizado por tipo, tamanho e relação com a release ativa |
| `/var/cache` | Não sabemos que parte é recuperação útil | Inventário de primeiro/segundo nível e política de retenção |
| `/tmp` e `/var/tmp` | Entradas systemd e sockets estavam ativos | Reavaliar somente após reboot/stop controlado, nunca por idade isolada |
| `snapshots`, `archives`, `quarantine`, `catalogue` vazios | Estado vazio atual não significa que devam ser removidos | Nenhuma; preservar os diretórios estruturais |
| Generation IDs APX | Visíveis, mas não transcritos com confiança das fotografias | Captura textual sanitizada ou fotografia mais nítida, caso sejam exigidos no repositório |

## 3. Fase efetivamente evidenciada

### Fases 1–8

O estado observado é compatível com a declaração de conclusão:

- host físico correto;
- APX instalado e saudável;
- Hub e Development registados e em execução;
- separação de papéis válida;
- Development sem `apx` e sem executor socket;
- Hub sem ferramentas de desenvolvimento, clones, Ollama ou Qwen;
- repositório no local esperado;
- GitHub e Codex autenticados;
- releases e mounts APX presentes;
- quotas Btrfs ativas e consistentes.

A auditoria não reexecutou os testes originais de cada fase. Portanto:

> **As Fases 1–8 estão refletidas pelo estado atual observado, mas esta sessão não constitui repetição integral de todas as provas históricas dessas fases.**

### Fase 9

**Estado: deliberadamente parcial e bloqueado para conclusão.**

Evidenciado:

- Ollama `0.32.0-1`;
- Qwen Code `0.19.2-1`;
- serviço Ollama enabled e active;
- utilizador/grupo `ollama`;
- `ExecStart=/usr/bin/ollama serve`;
- `OLLAMA_MODELS=/var/lib/ollama`;
- listener apenas em `127.0.0.1:11434`;
- `ollama list` sem modelos;
- `/var/lib/ollama` ausente;
- `/home/apx/.ollama` e `/root/.ollama` ausentes;
- `/usr/share/ollama` vazio, 4 KiB;
- nenhuma evidência de blobs, manifests ou downloads parciais de modelos;
- nenhum ficheiro acima de 100 MiB associado ao Ollama.

Ainda pendente:

- prova dos limites Development de 16/8 GiB via fluxo v3;
- prova ativa de inacessibilidade host/Hub → Ollama;
- política aprovada para enablement/activity e teardown;
- projeto separado do SSD externo, caso modelos venham a residir nele;
- qualquer teste com modelo permanece não aplicável enquanto nenhum modelo for admitido.

### Fase 10

**Estado: bloqueada.**

Bloqueios atuais:

1. não há prova nesta sessão de stop/start completo do Development preservando repositório, GitHub e Codex;
2. limites 16/8 GiB não ficaram visíveis;
3. `/root/apx-bootstrap-recovery` ainda não foi classificado em termos de dependência de recuperação;
4. a release antiga do Codex requer política/revisão própria;
5. planos, journal e releases APX antigas podem ter valor de rollback;
6. o serviço Ollama está ativo e enabled, exigindo decisão explícita de Fase 9;
7. a prova ativa de isolamento do listener não foi concluída;
8. nenhuma lista exata de remoção foi aprovada pelo owner.

## 4. Observações falhadas, indisponíveis ou corrigidas

| Observação | Resultado |
|---|---|
| `hostnamectl --statics` | Erro de escrita; corrigido com `hostnamectl --static` |
| `machinectl list --json` | Opção não suportada; recolhido com `machinectl list` |
| `pacaman -Qqe` | Erro de escrita; corrigido |
| `pacman-Qqe` | Faltou espaço; corrigido |
| Primeiro `git log` | Falhou porque `less` não existe; repetido com `GIT_PAGER=cat` |
| Primeira listagem das releases Codex | Erro em `-maxdepth`; corrigido |
| Primeiro `df -h home/apx` | Caminho sem `/`; corrigido |
| `machinectl show apx-development -p Address` | Sem saída |
| `btrfs qgroup show -reF /var/lib/apx` | Visibilidade incompleta; só mostrou `0/261` |
| Generation IDs na imagem final | Não transcritos por legibilidade insuficiente |
| Prova ativa host/Hub → Ollama | Não concluída |
| Stop/start completo do Development | Não executado nesta sessão read-only |
| Metadados completos de `/tmp` e `/var/tmp` | Nomes observados, mas não recolhidos com todos os campos originalmente pedidos |
| Inventário integral de todos os pacotes do Hub e Development | Pacotes explícitos recolhidos; a lista completa `pacman -Q` interna não foi preservada integralmente em evidência textual |

Houve também uma interpretação incorreta durante a sessão relativamente à fotografia dos ficheiros grandes. A fotografia mostrava dois binários Codex acima de 100 MiB; a classificação foi corrigida.

## 5. Plano de limpeza proposto — sem comandos

Nenhuma linha abaixo é autorização.

| Objeto | Ação proposta para revisão |
|---|---|
| `/root/apx-bootstrap` | Considerar remoção apenas após confirmar que o repositório GitHub, o clone de recuperação e os procedimentos atuais substituem integralmente a sua função |
| Pacote `git` no host | Considerar remoção apenas depois de confirmar que nenhum recovery/bootstrap/update depende de Git no host |
| `/root/apx-bootstrap-recovery` | Preservar; abrir análise separada de recuperação, remoto, commit e referências |
| Codex release `0.114.4-…` | Preservar até confirmar política de rollback e funcionamento da release 0.114.5 após stop/start |
| `/var/cache` | Preservar; criar proposta separada por subdiretório, retenção e valor de recuperação |
| Releases APX antigas | Preservar; cruzar com manifests, plans, journal e scripts antes de qualquer proposta |
| Planos APX | Preservar; classificar individualmente como ativo, concluído, recovery ou desconhecido |
| Journal APX | Preservar integralmente |
| Ollama package/service | Não alterar até a Fase 9 decidir o estado steady-state sem modelo |
| `/usr/share/ollama` | Preservar como objeto pertencente ao pacote |
| Estruturas vazias APX | Preservar |
| Diretórios temporários systemd | Preservar durante esta sessão; reavaliar apenas como parte de procedimento de lifecycle aprovado |

A lista inicial potencialmente elegível para uma futura sessão aprovada continua limitada a:

1. `/root/apx-bootstrap`
2. pacote `git` do host

Todos os restantes objetos exigem instruções próprias e revisão independente.

## 6. Plano exato de verificação pós-limpeza

Após uma futura aprovação separada:

1. Reconfirmar fabricante, produto, board, hostname e marcador físico.
2. Reconfirmar que os alvos têm exatamente os mesmos paths, tipos, owners e funções observados.
3. Confirmar o commit e remoto de `/root/apx-bootstrap` antes da ação.
4. Confirmar que `/root/apx-bootstrap-recovery` permanece intacto.
5. Confirmar que o repositório em Development está limpo e sincronizado.
6. Confirmar `gh auth status` e `codex login status`.
7. Confirmar que Codex resolve para a release 0.114.5 ou para a release então aprovada.
8. Executar o stop/start completo de Development através do procedimento APX aprovado.
9. Revalidar repositório, GitHub e Codex após o ciclo.
10. Executar `apx status`, listagem de Environments e unidades falhadas.
11. Revalidar registrations, releases, subvolumes e mounts.
12. Executar a prova de quotas através do script v3 revisto e demonstrar os limites 16/8 GiB.
13. Revalidar Hub: sem Git, GH, compilers, Node, npm, Codex, Ollama, Qwen ou clones.
14. Revalidar host: sem serviços de desenvolvimento e sem objetos além dos explicitamente preservados.
15. Revalidar Development: sem executor socket e sem comando `apx`.
16. Revalidar Ollama: package/version, enablement, activity, listener, user, models e diretórios.
17. Demonstrar que host e Hub não conseguem alcançar o listener do Development.
18. Registar exatamente os objetos removidos e os bytes libertados.
19. Confirmar que rollback e recuperação continuam possíveis.
20. Parar imediatamente perante qualquer drift, objeto desconhecido ou falha.

## 7. Versão sanitizada para o repositório

```text
APX Physical Pilot State and Cleanup Audit v1
Evidence date: 2026-07-17
Session: owner-run read-only evidence collection
Mutation performed: none

Identity:
- root on physical host
- hostname apx-host
- virtualization none
- vendor LENOVO
- product 82JU
- board LNVNB161216
- marker profile=apx-physical-headless-pilot-v1

APX:
- state root /var/lib/apx on Btrfs @apx
- total observed size 7.0 GiB
- host healthy
- hub running
- development running
- no failed host units
- Btrfs quotas enabled, full accounting, not inconsistent
- detailed Development qgroup limits not visible through /var/lib/apx

Hub:
- hostname apx-hub
- explicit packages: base, python, systemd
- no git, gh, gcc, node, npm, codex, ollama, or qwen commands
- no Git repositories
- only system base services/listeners observed

Development:
- hostname apx-development
- executor socket absent
- apx command absent
- one repository: /home/apx/work/apx
- branch master, clean working tree
- remote origin points to GitHub repository
- git fsck completed without errors
- GitHub authenticated
- Codex authenticated using ChatGPT
- explicit packages:
  base, base-devel, bubblewrap, git, github-cli,
  nodejs, npm, ollama, python, qwen-code, systemd
- no orphan packages

Ollama:
- package 0.32.0-1
- qwen-code 0.19.2-1
- command /usr/bin/ollama
- service enabled and active
- service user/group ollama
- ExecStart /usr/bin/ollama serve
- OLLAMA_MODELS=/var/lib/ollama
- listener 127.0.0.1:11434 only
- ollama list contains zero models
- /var/lib/ollama absent
- /home/apx/.ollama absent
- /root/.ollama absent
- /usr/share/ollama present but empty, 4 KiB

Storage:
- /home/apx 1019 MiB
- /home/apx/.codex 831 MiB
- repository 29 MiB
- Codex releases 0.114.4 and 0.114.5 present
- active Codex release 0.114.5
- previous 0.114.4 release preserved for review
- /var/cache 708 MiB
- journals 8 MiB
- no coredumps
- no Ollama model files or partial model downloads observed

Host temporary/recovery material:
- /root/apx-bootstrap, 20 MiB
- /root/apx-bootstrap-recovery, 21 MiB
- host git explicitly installed
- no foreign packages
- no package orphans

Phase assessment:
- Phases 1-8 reflected by current observed state
- Phase 9 partially evidenced and deliberately incomplete
- Phase 10 blocked
- no cleanup authorized

Potential future approved targets:
- /root/apx-bootstrap
- host git package

Preserve:
- /root/apx-bootstrap-recovery
- APX plans, journal, releases, registrations and qgroups
- Codex previous release pending rollback review
- all unknown objects
```

## 8. Conclusão

O piloto está saudável e isolado no estado observado, mas ainda não existe evidência suficiente para iniciar a Fase 10. A máquina deve permanecer inalterada até revisão no repositório e aprovação explícita de uma lista exata de alvos.
