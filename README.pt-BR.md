# Prospero.Eden Encore — Português (Brasil)

> Emulação comunitária para jogar no PS5 na sala · [English (default)](README.md) · [Todos os idiomas](LANGUAGES.md)

O Encore é um fork comunitário independente, com launcher para controle, biblioteca de jogos, ajustes gráficos e ferramentas de diagnóstico. Não é um produto oficial da Sony ou Nintendo.

## Primeiros passos

1. Baixe o pacote completo das Encore Releases e confira a integridade do arquivo.
2. Faça backup de PPSA99008, dos dados /data/prosperoeden e do armazenamento externo.
3. Copie toda a pasta PPSA99008 para /data/homebrew/PPSA99008/; só eboot.bin não é suficiente.
4. Abra o Encore, confira Settings → Storage e Language, e use apenas arquivos obtidos legalmente.

[Migração do projeto original](docs/i18n/INSTALL.pt-BR.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migração do projeto original

Encore e ProsperoEden nativo usam o mesmo ID PPSA99008; não são dois aplicativos independentes. Substitua os arquivos completos do aplicativo e preserve saves, configurações, jogos e chaves em /data/prosperoeden. Faça backup da pasta antiga assets/ antes de migrar.

**ID do aplicativo :** `PPSA99008`. **Aplicativo :** `/data/homebrew/PPSA99008/`. **Dados persistentes :** `/data/prosperoeden/`.

[Migração do projeto original — passo a passo](docs/i18n/INSTALL.pt-BR.md) · [Instalação completa em inglês](INSTALL.md)

## Compatibilidade e limitações

O único firmware testado com Encore em um PS5 real é 13.60. Versões anteriores talvez funcionem, mas não foram verificadas e não há firmware mínimo confirmado. Alguns jogos ainda apresentam travamentos, HUD atrasado, botões incorretos e congelamentos em pausas. Build verde não garante compatibilidade.

O código em desenvolvimento reconhece NSP/XCI e, de forma experimental, NSZ/XCZ. Arquivos diretos NRO/NSO/NCA/NAX/KIP precisam de conteúdo adequado; reconhecer a extensão não garante inicialização.

## Perguntas frequentes

Switch 2 é uma pesquisa em outra branch e não está disponível no lançamento PS5. Geração de quadros e atualizações automáticas são planos ainda não lançados.

Se o menu continua em inglês, selecione Settings → Language e confira a pasta ui/lang/ completa.

## Comunidade e créditos

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

O projeto não fornece jogos, chaves nem firmware. Não publique dados pessoais em relatórios de erros.

> Esta tradução cobre o essencial. O README em inglês continua sendo a referência técnica completa; testes de código não comprovam o desempenho no PS5.
