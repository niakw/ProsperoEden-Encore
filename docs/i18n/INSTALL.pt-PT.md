<!-- Encore user guide crosslinks 2026-11-09 -->
> **Definições:** [Definições](SETTINGS.pt-PT.md) · [Resolução de problemas](TROUBLESHOOTING.pt-PT.md) · [Apoio](SUPPORT.pt-PT.md) · [Acessibilidade](ACCESSIBILITY.pt-PT.md) · [Languages](../../LANGUAGES.md)
>
> O último pacote PS5 público efectivamente compilado é de 15 de outubro de 2026. A publicação de 30 de outubro foi uma cópia. O novo rascunho de pré-lançamento não inclui binários nem compatibilidade da segunda geração validada na consola.

# Prospero.Eden Encore — Migração do projecto original (Português (Portugal))

[← Português (Portugal)](README.pt-PT.md) · [Instalação completa em inglês](../../INSTALL.md) · [Todos os idiomas](../../LANGUAGES.md)

## Primeiros passos

1. Descarrega o pacote completo das Encore Releases e verifica a integridade.
2. Faz uma cópia de segurança de PPSA99008, dos dados /data/prosperoeden e do armazenamento externo.
3. Copia a pasta PPSA99008 inteira para /data/homebrew/PPSA99008/; apenas eboot.bin não chega.
4. Inicia o Encore, verifica Settings → Storage e Language e utiliza apenas ficheiros obtidos legalmente.

## Aplicação / PPSA99008

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent user files
/data/prosperoeden/keys/          # legally obtained keys
/data/prosperoeden/firmware/      # compatible firmware files
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # game updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # diagnostics
```

## Migração do projecto original

O Encore e o ProsperoEden original usam o mesmo ID PPSA99008 e não são instalações independentes. Substitui os ficheiros completos da aplicação, preservando gravações, definições, jogos e chaves em /data/prosperoeden. Guarda a antiga pasta assets/ antes da migração.

**Importante:** nunca apagues `/data/prosperoeden/` nem formates o armazenamento externo numa actualização. Faz cópia de segurança e preserva gravações e chaves.

## Compatibilidade e limites

A única versão de firmware testada com Encore numa PS5 real é a 13.60. As anteriores podem funcionar, mas ainda não foram verificadas e não existe um mínimo confirmado. Alguns jogos apresentam soluços, HUD atrasado, comandos incorrectos e bloqueios nas pausas. Uma compilação bem-sucedida não prova a jogabilidade.

## Perguntas frequentes

Se o menu continuar em inglês, selecciona Settings → Language e verifica a pasta ui/lang/ completa.

Se um jogo deixar de arrancar após uma alteração, experimenta **Safe Launch** durante essa sessão, sem apagar gravações. Consulta a [instalação ZIP/FFPFSC](../../INSTALL.md), a [resolução de problemas](../../TROUBLESHOOTING.md) e o [suporte](../../SUPPORT.md).

O projecto não fornece jogos, chaves nem firmware. Não publiques dados pessoais nos relatórios.
