# Prospero.Eden Encore — Português (Portugal)

> Emulação comunitária PS5 para jogar na sala · [English (default)](README.md) · [Todos os idiomas](LANGUAGES.md)

O Encore é um projecto comunitário independente, com interface para comando, biblioteca de jogos, opções de vídeo e ferramentas de diagnóstico. Não é um produto oficial da Sony ou Nintendo.

## Primeiros passos

1. Descarrega o pacote completo das Encore Releases e verifica a integridade.
2. Faz uma cópia de segurança de PPSA99008, dos dados /data/prosperoeden e do armazenamento externo.
3. Copia a pasta PPSA99008 inteira para /data/homebrew/PPSA99008/; apenas eboot.bin não chega.
4. Inicia o Encore, verifica Settings → Storage e Language e utiliza apenas ficheiros obtidos legalmente.

[Migração do projecto original](docs/i18n/INSTALL.pt-PT.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migração do projecto original

O Encore e o ProsperoEden original usam o mesmo ID PPSA99008 e não são instalações independentes. Substitui os ficheiros completos da aplicação, preservando gravações, definições, jogos e chaves em /data/prosperoeden. Guarda a antiga pasta assets/ antes da migração.

**ID da aplicação :** `PPSA99008`. **Aplicação :** `/data/homebrew/PPSA99008/`. **Dados persistentes :** `/data/prosperoeden/`.

[Migração do projecto original — passo a passo](docs/i18n/INSTALL.pt-PT.md) · [Instalação completa em inglês](INSTALL.md)

## Compatibilidade e limites

A única versão de firmware testada com Encore numa PS5 real é a 13.60. As anteriores podem funcionar, mas ainda não foram verificadas e não existe um mínimo confirmado. Alguns jogos apresentam soluços, HUD atrasado, comandos incorrectos e bloqueios nas pausas. Uma compilação bem-sucedida não prova a jogabilidade.

O código em desenvolvimento reconhece NSP/XCI e, experimentalmente, NSZ/XCZ. Os ficheiros directos NRO/NSO/NCA/NAX/KIP exigem conteúdos compatíveis; reconhecer a extensão não garante que o jogo arranque.

## Perguntas frequentes

A Switch 2 é investigada numa ramificação separada e não está incluída no lançamento PS5. A geração de fotogramas e as actualizações automáticas estão planeadas, mas não foram lançadas.

Se o menu continuar em inglês, selecciona Settings → Language e verifica a pasta ui/lang/ completa.

## Comunidade e créditos

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

O projecto não fornece jogos, chaves nem firmware. Não publiques dados pessoais nos relatórios.

> Esta tradução cobre o essencial. O README inglês continua a ser a referência técnica completa; testes de código não demonstram o desempenho real na PS5.
