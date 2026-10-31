# Prospero.Eden Encore — Migração do projeto original (Português (Brasil))

[← Português (Brasil)](../../README.pt-BR.md) · [Full English installation guide](../../INSTALL.md) · [Languages](../../LANGUAGES.md)

## Primeiros passos

1. Baixe o pacote completo das Encore Releases e confira a integridade do arquivo.
2. Faça backup de PPSA99008, dos dados /data/prosperoeden e do armazenamento externo.
3. Copie toda a pasta PPSA99008 para /data/homebrew/PPSA99008/; só eboot.bin não é suficiente.
4. Abra o Encore, confira Settings → Storage e Language, e use apenas arquivos obtidos legalmente.

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

## Migração do projeto original

Encore e ProsperoEden nativo usam o mesmo ID PPSA99008; não são dois aplicativos independentes. Substitua os arquivos completos do aplicativo e preserve saves, configurações, jogos e chaves em /data/prosperoeden. Faça backup da pasta antiga assets/ antes de migrar.

**Important:** Never delete `/data/prosperoeden/` or format external storage as a normal update step. Back up before migration; do not overwrite existing saves or keys.

## Compatibilidade e limitações

O único firmware testado com Encore em um PS5 real é 13.60. Versões anteriores talvez funcionem, mas não foram verificadas e não há firmware mínimo confirmado. Alguns jogos ainda apresentam travamentos, HUD atrasado, botões incorretos e congelamentos em pausas. Build verde não garante compatibilidade.

## Perguntas frequentes

Se o menu continua em inglês, selecione Settings → Language e confira a pasta ui/lang/ completa.

If a title stops booting after changing settings, use **Safe Launch** for a temporary reset. For ZIP and FFPFSC/ShadowMountPlus methods see [INSTALL.md](../../INSTALL.md); for error details see [Troubleshooting](../../TROUBLESHOOTING.md) and [Support](../../SUPPORT.md).

O projeto não fornece jogos, chaves nem firmware. Não publique dados pessoais em relatórios de erros.
