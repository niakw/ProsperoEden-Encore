# Eden Encore — Resolução de problemas · Português (Portugal)

[Visão geral](README.pt-PT.md) · [Instalação e actualização](INSTALL.pt-PT.md) · [Definições](SETTINGS.pt-PT.md) · [Resolução de problemas](TROUBLESHOOTING.pt-PT.md) · [Apoio](SUPPORT.pt-PT.md) · [Acessibilidade](ACCESSIBILITY.pt-PT.md) · [Languages](../../LANGUAGES.md)

Se a aplicação não arrancar, verifica eboot.bin, sce_sys e ui/lang. Se não aparecerem jogos, confirma roms na raiz de armazenamento seleccionada. Se o menu permanecer em inglês, verifica os catálogos de tradução. Safe Launch repõe as definições de um jogo sem eliminar gravações.

## Instalação e actualização

Descarrega um pacote efectivamente publicado em Releases e guarda primeiro uma cópia da aplicação e dos dados. Em ZIP/FTP, copia toda a pasta PPSA99008 para /data/homebrew/PPSA99008/. Não mistures ZIP/FTP com FFPFSC/ShadowMountPlus; verifica SHA-256 quando disponibilizado.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Definições

O perfil recomendado utiliza Vulkan, saída de TV a 1440p, escala interna de jogo 1.25x, FSR 1 espacial com nitidez de 50%, FXAA e 60 Hz. A saída da televisão difere da resolução interna do jogo. A geração de fotogramas não aumenta a velocidade de simulação do jogo.

## Apoio

Num GitHub Issue indica a versão do Encore, firmware PS5, passos para reproduzir, definições pertinentes e registos anonimizados. Nunca publiques chaves, gravações ou dados pessoais.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Nunca apagues /data/prosperoeden/: pode conter gravações, definições e chaves. Guarda também uma cópia do armazenamento externo.

---

O último pacote PS5 público efectivamente compilado é de 15 de outubro de 2026. A publicação de 30 de outubro foi uma cópia. O novo rascunho de pré-lançamento não inclui binários nem compatibilidade da segunda geração validada na consola.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)