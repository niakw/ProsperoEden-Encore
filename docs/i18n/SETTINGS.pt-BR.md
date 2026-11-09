# Eden Encore — Configurações · Português (Brasil)

[Visão geral](README.pt-BR.md) · [Instalação e atualização](INSTALL.pt-BR.md) · [Configurações](SETTINGS.pt-BR.md) · [Solução de problemas](TROUBLESHOOTING.pt-BR.md) · [Suporte](SUPPORT.pt-BR.md) · [Acessibilidade](ACCESSIBILITY.pt-BR.md) · [Languages](../../LANGUAGES.md)

O perfil recomendado usa Vulkan, saída de TV 1440p, escala interna de jogo 1.25x, FSR 1 espacial com nitidez 50%, FXAA e 60 Hz. A saída da TV é diferente da resolução interna do jogo. A geração de quadros não aumenta a velocidade de simulação do jogo.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** O perfil recomendado usa Vulkan, saída de TV 1440p, escala interna de jogo 1.25x, FSR 1 espacial com nitidez 50%, FXAA e 60 Hz. A saída da TV é diferente da resolução interna do jogo. A geração de quadros não aumenta a velocidade de simulação do jogo.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Acessibilidade

Texto ampliado, alto contraste e movimento reduzido podem ser ativados separadamente em Acessibilidade; todos começam desligados. A acessibilidade do iniciador não garante a acessibilidade de cada jogo.

## Solução de problemas

Se o aplicativo não iniciar, confira eboot.bin, sce_sys e ui/lang. Caso os jogos sumam, verifique roms na raiz de armazenamento selecionada. Se o menu continuar em inglês, confira os arquivos de idioma. Safe Launch restaura as configurações de um jogo sem apagar os saves.

Nunca apague /data/prosperoeden/: a pasta pode conter saves, configurações e chaves. Salve também uma cópia do armazenamento externo.

---

O último pacote PS5 público realmente compilado é de 15 de outubro de 2026; a publicação de 30 de outubro foi uma cópia. O novo rascunho de pré-lançamento não possui binários nem jogos de segunda geração validados no console.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)