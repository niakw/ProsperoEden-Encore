# Prospero.Eden Encore — Migração do projeto original (Português (Brasil))

[← Português (Brasil)](README.pt-BR.md) · [Instalação completa em inglês](../../INSTALL.md) · [Todos os idiomas](../../LANGUAGES.md)

## Primeiros passos

1. Baixe o pacote completo das Encore Releases e confira a integridade do arquivo.
2. Faça backup de PPSA99008, dos dados /data/prosperoeden e do armazenamento externo.
3. Copie toda a pasta PPSA99008 para /data/homebrew/PPSA99008/; só eboot.bin não é suficiente.
4. Abra o Encore, confira Settings → Storage e Language, e use apenas arquivos obtidos legalmente.

## Aplicativo / PPSA99008

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

**Importante:** Nunca apague `/data/prosperoeden/` nem formate o armazenamento externo durante uma atualização. Faça backup primeiro e preserve saves e chaves.

## Compatibilidade e limitações

O único firmware testado com Encore em um PS5 real é 13.60. Versões anteriores talvez funcionem, mas não foram verificadas e não há firmware mínimo confirmado. Alguns jogos ainda apresentam travamentos, HUD atrasado, botões incorretos e congelamentos em pausas. Build verde não garante compatibilidade.

## Perguntas frequentes

Se o menu continua em inglês, selecione Settings → Language e confira a pasta ui/lang/ completa.

Se um jogo parar de iniciar após mudar opções, use **Safe Launch** temporariamente sem apagar saves. Veja a [instalação ZIP/FFPFSC](../../INSTALL.md), a [solução de problemas](../../TROUBLESHOOTING.md) e o [suporte](../../SUPPORT.md).

O projeto não fornece jogos, chaves nem firmware. Não publique dados pessoais em relatórios de erros.
