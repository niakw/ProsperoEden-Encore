# Prospero.Eden Encore — Português (Portugal)

> Emulação comunitária PS5 para jogar na sala · [English (default)](README.md) · [All 18 launcher language choices](LANGUAGES.md)

Emulação comunitária PS5 para jogar na sala. Encore is an independent community fork with a controller-friendly launcher, game library, graphics settings and diagnostics, not an official Sony or Nintendo product.

## Primeiros passos

1. Descarrega o pacote completo das Encore Releases e verifica a integridade.
2. Faz uma cópia de segurança de PPSA99008, dos dados /data/prosperoeden e do armazenamento externo.
3. Copia a pasta PPSA99008 inteira para /data/homebrew/PPSA99008/; apenas eboot.bin não chega.
4. Inicia o Encore, verifica Settings → Storage e Language e utiliza apenas ficheiros obtidos legalmente.

[Migração do projecto original](docs/i18n/INSTALL.pt-PT.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migração do projecto original

O Encore e o ProsperoEden original usam o mesmo ID PPSA99008 e não são instalações independentes. Substitui os ficheiros completos da aplicação, preservando gravações, definições, jogos e chaves em /data/prosperoeden. Guarda a antiga pasta assets/ antes da migração.

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[Migração do projecto original — step-by-step](docs/i18n/INSTALL.pt-PT.md) · [Full installation instructions in English](INSTALL.md)

## Compatibilidade e limites

A única versão de firmware testada com Encore numa PS5 real é a 13.60. As anteriores podem funcionar, mas ainda não foram verificadas e não existe um mínimo confirmado. Alguns jogos apresentam soluços, HUD atrasado, comandos incorrectos e bloqueios nas pausas. Uma compilação bem-sucedida não prova a jogabilidade.

Content formats in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee that a complete game will start.

## Perguntas frequentes

A Switch 2 é investigada numa ramificação separada e não está incluída no lançamento PS5. A geração de fotogramas e as actualizações automáticas estão planeadas, mas não foram lançadas.

Se o menu continuar em inglês, selecciona Settings → Language e verifica a pasta ui/lang/ completa.

## Community and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

O projecto não fornece jogos, chaves nem firmware. Não publiques dados pessoais nos relatórios.

> This translation is a concise guide for the selected launcher language. For complete technical information, use the English README and linked guides. No console performance claim is implied.
