# Prospero.Eden Encore — Migração do projecto original (Português (Portugal))

[← Português (Portugal)](../../README.pt-PT.md) · [Full English installation guide](../../INSTALL.md) · [Languages](../../LANGUAGES.md)

## Primeiros passos

1. Descarrega o pacote completo das Encore Releases e verifica a integridade.
2. Faz uma cópia de segurança de PPSA99008, dos dados /data/prosperoeden e do armazenamento externo.
3. Copia a pasta PPSA99008 inteira para /data/homebrew/PPSA99008/; apenas eboot.bin não chega.
4. Inicia o Encore, verifica Settings → Storage e Language e utiliza apenas ficheiros obtidos legalmente.

## Paths / PPSA99008

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

**Important:** Never delete `/data/prosperoeden/` or format external storage as a normal update step. Back up before migration; do not overwrite existing saves or keys.

## Compatibilidade e limites

A única versão de firmware testada com Encore numa PS5 real é a 13.60. As anteriores podem funcionar, mas ainda não foram verificadas e não existe um mínimo confirmado. Alguns jogos apresentam soluços, HUD atrasado, comandos incorrectos e bloqueios nas pausas. Uma compilação bem-sucedida não prova a jogabilidade.

## Perguntas frequentes

Se o menu continuar em inglês, selecciona Settings → Language e verifica a pasta ui/lang/ completa.

If a title stops booting after changing settings, use **Safe Launch** for a temporary reset. For ZIP and FFPFSC/ShadowMountPlus methods see [INSTALL.md](../../INSTALL.md); for error details see [Troubleshooting](../../TROUBLESHOOTING.md) and [Support](../../SUPPORT.md).

O projecto não fornece jogos, chaves nem firmware. Não publiques dados pessoais nos relatórios.
