<table width="100%">
  <tr><td align="center">
    <strong>🌐 LANGUAGES</strong> &nbsp; · &nbsp; <a href="../../README.md">English</a> &nbsp; · &nbsp; <a href="../../README.md">English UK</a> &nbsp; · &nbsp; <a href="README.zh-Hans.md">简体中文</a> &nbsp; · &nbsp; <a href="README.zh-Hant.md">繁體中文</a> &nbsp; · &nbsp; <a href="README.es-419.md">Español LatAm</a> &nbsp; · &nbsp; <a href="README.es.md">Español ES</a> &nbsp; · &nbsp; <a href="README.fr.md">Français</a> &nbsp; · &nbsp; <a href="README.fr-CA.md">Français CA</a> &nbsp; · &nbsp; <strong>Português BR</strong><br>
    <a href="README.pt-PT.md">Português PT</a> &nbsp; · &nbsp; <a href="README.ru.md">Русский</a> &nbsp; · &nbsp; <a href="README.de.md">Deutsch</a> &nbsp; · &nbsp; <a href="README.ja.md">日本語</a> &nbsp; · &nbsp; <a href="README.ko.md">한국어</a> &nbsp; · &nbsp; <a href="README.it.md">Italiano</a> &nbsp; · &nbsp; <a href="README.th.md">ไทย</a> &nbsp; · &nbsp; <a href="README.pl.md">Polski</a> &nbsp; · &nbsp; <a href="README.nl.md">Nederlands</a> &nbsp; · &nbsp; <a href="../../LANGUAGES.md"><strong>All languages</strong></a>
  </td></tr>
</table>

<table width="100%">
  <tr>
    <td width="21%" align="center" valign="middle"><a href="../../README.md"><img src="../../assets/icon0.png" alt="Prospero.Eden Encore logo" width="148"></a></td>
    <td width="79%" align="left" valign="middle">
      <h1>Prospero.Eden Encore</h1>
      <p><strong>Emulação comunitária para jogar no PS5 na sala</strong></p>
      <p>O Encore é um fork comunitário independente, com launcher para controle, biblioteca de jogos, ajustes gráficos e ferramentas de diagnóstico. Não é um produto oficial da Sony ou Nintendo.</p>
      <p><kbd>Firmware 13.60 · testado no PS5</kbd> &nbsp; <kbd>Vulkan + OpenGL</kbd> &nbsp; <kbd>Interface TV</kbd> &nbsp; <kbd>Dynarmic</kbd></p>
    </td>
  </tr>
</table>

<table width="100%">
  <tr>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/releases"><strong>Baixar</strong></a></td>
    <td align="center"><a href="INSTALL.pt-BR.md"><strong>Instalar</strong></a></td>
    <td align="center"><a href="#getting-started"><strong>Começar</strong></a></td>
    <td align="center"><a href="#compatibility"><strong>Compatibilidade</strong></a></td>
    <td align="center"><a href="#faq"><strong>Perguntas</strong></a></td>
    <td align="center"><a href="../../TROUBLESHOOTING.md"><strong>Ajuda</strong></a></td>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md"><strong>Roadmap</strong></a></td>
  </tr>
</table>

<a id="getting-started"></a>
## Primeiros passos

1. Baixe o pacote completo das Encore Releases e confira a integridade do arquivo.
2. Faça backup de PPSA99008, dos dados /data/prosperoeden e do armazenamento externo.
3. Copie toda a pasta PPSA99008 para /data/homebrew/PPSA99008/; só eboot.bin não é suficiente.
4. Abra o Encore, confira Settings → Storage e Language, e use apenas arquivos obtidos legalmente.

[Migração do projeto original](INSTALL.pt-BR.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](../../SUPPORT.md)

## Migração do projeto original

Encore e ProsperoEden nativo usam o mesmo ID PPSA99008; não são dois aplicativos independentes. Substitua os arquivos completos do aplicativo e preserve saves, configurações, jogos e chaves em /data/prosperoeden. Faça backup da pasta antiga assets/ antes de migrar.

**ID do aplicativo :** `PPSA99008`. **Aplicativo :** `/data/homebrew/PPSA99008/`. **Dados persistentes :** `/data/prosperoeden/`.

[Migração do projeto original — passo a passo](INSTALL.pt-BR.md) · [Instalação completa em inglês](../../INSTALL.md)

<a id="compatibility"></a>
## Compatibilidade e limitações

O único firmware testado com Encore em um PS5 real é 13.60. Versões anteriores talvez funcionem, mas não foram verificadas e não há firmware mínimo confirmado. Alguns jogos ainda apresentam travamentos, HUD atrasado, botões incorretos e congelamentos em pausas. Build verde não garante compatibilidade.

O código em desenvolvimento reconhece NSP/XCI e, de forma experimental, NSZ/XCZ. Arquivos diretos NRO/NSO/NCA/NAX/KIP precisam de conteúdo adequado; reconhecer a extensão não garante inicialização.

<a id="faq"></a>
## Perguntas frequentes

Switch 2 é uma pesquisa em outra branch e não está disponível no lançamento PS5. Geração de quadros e atualizações automáticas são planos ainda não lançados.

Se o menu continua em inglês, selecione Settings → Language e confira a pasta ui/lang/ completa.

## Comunidade e créditos

[Complete English reference](../../README.md) · [Settings](../../SETTINGS.md) · [Accessibility](../../ACCESSIBILITY.md) · [Troubleshooting](../../TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](../../README.md#credits) · [GPL-3.0-or-later](../../LICENSE).

O projeto não fornece jogos, chaves nem firmware. Não publique dados pessoais em relatórios de erros.

> Esta tradução cobre o essencial. O README em inglês continua sendo a referência técnica completa; testes de código não comprovam o desempenho no PS5.
