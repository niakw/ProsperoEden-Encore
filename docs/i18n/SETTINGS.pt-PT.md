# Eden Encore — Definições · Português (Portugal)

[Visão geral](README.pt-PT.md) · [Instalação e actualização](INSTALL.pt-PT.md) · [Definições](SETTINGS.pt-PT.md) · [Resolução de problemas](TROUBLESHOOTING.pt-PT.md) · [Apoio](SUPPORT.pt-PT.md) · [Acessibilidade](ACCESSIBILITY.pt-PT.md) · [Languages](../../LANGUAGES.md)

O perfil recomendado utiliza Vulkan, saída de TV a 1440p, escala interna de jogo 1.25x, FSR 1 espacial com nitidez de 50%, FXAA e 60 Hz. A saída da televisão difere da resolução interna do jogo. A geração de fotogramas não aumenta a velocidade de simulação do jogo.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** O perfil recomendado utiliza Vulkan, saída de TV a 1440p, escala interna de jogo 1.25x, FSR 1 espacial com nitidez de 50%, FXAA e 60 Hz. A saída da televisão difere da resolução interna do jogo. A geração de fotogramas não aumenta a velocidade de simulação do jogo.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Acessibilidade

Texto maior, contraste elevado e redução de movimento podem ser activados separadamente em Acessibilidade e estão desligados por defeito. A acessibilidade do lançador não garante acessibilidade em todos os jogos.

## Resolução de problemas

Se a aplicação não arrancar, verifica eboot.bin, sce_sys e ui/lang. Se não aparecerem jogos, confirma roms na raiz de armazenamento seleccionada. Se o menu permanecer em inglês, verifica os catálogos de tradução. Safe Launch repõe as definições de um jogo sem eliminar gravações.

Nunca apagues /data/prosperoeden/: pode conter gravações, definições e chaves. Guarda também uma cópia do armazenamento externo.

---

O último pacote PS5 público efectivamente compilado é de 15 de outubro de 2026. A publicação de 30 de outubro foi uma cópia. O novo rascunho de pré-lançamento não inclui binários nem compatibilidade da segunda geração validada na consola.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)