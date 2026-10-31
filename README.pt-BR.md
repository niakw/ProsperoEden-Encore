# Prospero.Eden Encore — Português (Brasil)

> Emulação comunitária para jogar no PS5 na sala · [English (default)](README.md) · [All 18 launcher language choices](LANGUAGES.md)

Emulação comunitária para jogar no PS5 na sala. Encore is an independent community fork with a controller-friendly launcher, game library, graphics settings and diagnostics, not an official Sony or Nintendo product.

## Primeiros passos

1. Baixe o pacote completo das Encore Releases e confira a integridade do arquivo.
2. Faça backup de PPSA99008, dos dados /data/prosperoeden e do armazenamento externo.
3. Copie toda a pasta PPSA99008 para /data/homebrew/PPSA99008/; só eboot.bin não é suficiente.
4. Abra o Encore, confira Settings → Storage e Language, e use apenas arquivos obtidos legalmente.

[Migração do projeto original](docs/i18n/INSTALL.pt-BR.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migração do projeto original

Encore e ProsperoEden nativo usam o mesmo ID PPSA99008; não são dois aplicativos independentes. Substitua os arquivos completos do aplicativo e preserve saves, configurações, jogos e chaves em /data/prosperoeden. Faça backup da pasta antiga assets/ antes de migrar.

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[Migração do projeto original — step-by-step](docs/i18n/INSTALL.pt-BR.md) · [Full installation instructions in English](INSTALL.md)

## Compatibilidade e limitações

O único firmware testado com Encore em um PS5 real é 13.60. Versões anteriores talvez funcionem, mas não foram verificadas e não há firmware mínimo confirmado. Alguns jogos ainda apresentam travamentos, HUD atrasado, botões incorretos e congelamentos em pausas. Build verde não garante compatibilidade.

Content formats in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee that a complete game will start.

## Perguntas frequentes

Switch 2 é uma pesquisa em outra branch e não está disponível no lançamento PS5. Geração de quadros e atualizações automáticas são planos ainda não lançados.

Se o menu continua em inglês, selecione Settings → Language e confira a pasta ui/lang/ completa.

## Community and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

O projeto não fornece jogos, chaves nem firmware. Não publique dados pessoais em relatórios de erros.

> This translation is a concise guide for the selected launcher language. For complete technical information, use the English README and linked guides. No console performance claim is implied.
