# Prospero.Eden Encore — 한국어

> 거실에서 즐기는 PS5 에뮬레이션 · [English (default)](README.md) · [All launcher languages](LANGUAGES.md)

거실에서 즐기는 PS5 에뮬레이션. Encore is an independent community emulator fork with a controller-first launcher, library, video settings and diagnostics. It is not an official Sony or Nintendo product.

## 시작하기

1. Encore Releases에서 전체 배포 패키지를 내려받고 체크섬을 확인하세요.
2. 기존 PPSA99008 앱 폴더, /data/prosperoeden 데이터, 외장 저장소를 백업하세요.
3. PPSA99008 폴더 전체를 /data/homebrew/PPSA99008/에 넣으세요. eboot.bin만 복사해서는 안 됩니다.
4. 실행 후 Settings → Storage 및 Language를 확인하고 합법적으로 보유한 파일만 사용하세요.

[기존 버전에서 이전하기](docs/i18n/INSTALL.ko.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## 기존 버전에서 이전하기

Encore와 원래 ProsperoEden은 동일한 앱 ID PPSA99008을 사용하므로 두 개의 별도 앱으로 설치할 수 없습니다. 앱 파일 전체만 교체하고 /data/prosperoeden의 저장 데이터, 설정, 게임, 키는 삭제하지 마세요. 이전 assets/에 사용자 데이터가 있다면 먼저 백업하세요.

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[기존 버전에서 이전하기 — step-by-step](docs/i18n/INSTALL.ko.md) · [Full installation instructions in English](INSTALL.md)

## 호환성과 알려진 문제

Encore를 실제 PS5에서 테스트한 펌웨어는 13.60뿐입니다. 구버전은 작동할 수 있으나 검증되지 않았고 최소 버전도 확정되지 않았습니다. 일부 게임은 끊김, HUD 표시 지연, 게임 중 버튼 오류, 일시 정지 시 멈춤이 남아 있습니다. 빌드 성공이 곧 게임 호환성을 뜻하지 않습니다.

Game container support in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee a title will run.

## 자주 묻는 질문

Switch 2는 별도 연구 브랜치에서 다루며 현재 PS5 버전에는 포함되지 않습니다. 프레임 생성과 자동 업데이트도 아직 출시되지 않은 계획 기능입니다.

메뉴가 영어로 나온다면 Settings → Language를 선택하고 ui/lang/ 폴더를 완전히 설치했는지 확인하세요.

## Links and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

이 프로젝트는 게임, 콘솔 키, 펌웨어를 제공하지 않습니다. 공개 오류 보고서에 개인정보를 올리지 마세요.

> This localized README covers essential user information. The English README remains the full technical reference; host tests do not certify PS5 performance.
