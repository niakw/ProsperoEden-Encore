# Prospero.Eden Encore — 기존 버전에서 이전하기 (한국어)

[← 한국어](../../README.ko.md) · [영어 전체 설치 안내](../../INSTALL.md) · [모든 언어](../../LANGUAGES.md)

## 시작하기

1. Encore Releases에서 전체 배포 패키지를 내려받고 체크섬을 확인하세요.
2. 기존 PPSA99008 앱 폴더, /data/prosperoeden 데이터, 외장 저장소를 백업하세요.
3. PPSA99008 폴더 전체를 /data/homebrew/PPSA99008/에 넣으세요. eboot.bin만 복사해서는 안 됩니다.
4. 실행 후 Settings → Storage 및 Language를 확인하고 합법적으로 보유한 파일만 사용하세요.

## PPSA99008 / storage

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent data
/data/prosperoeden/keys/          # legal keys
/data/prosperoeden/firmware/      # compatible firmware
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # logs
```

## 기존 버전에서 이전하기

Encore와 원래 ProsperoEden은 동일한 앱 ID PPSA99008을 사용하므로 두 개의 별도 앱으로 설치할 수 없습니다. 앱 파일 전체만 교체하고 /data/prosperoeden의 저장 데이터, 설정, 게임, 키는 삭제하지 마세요. 이전 assets/에 사용자 데이터가 있다면 먼저 백업하세요.

**중요:** 업데이트하면서 `/data/prosperoeden/`를 삭제하거나 외장 저장소를 포맷하지 마세요. 먼저 백업하고 저장 데이터와 키를 덮어쓰지 마세요.

## 호환성과 알려진 문제

Encore를 실제 PS5에서 테스트한 펌웨어는 13.60뿐입니다. 구버전은 작동할 수 있으나 검증되지 않았고 최소 버전도 확정되지 않았습니다. 일부 게임은 끊김, HUD 표시 지연, 게임 중 버튼 오류, 일시 정지 시 멈춤이 남아 있습니다. 빌드 성공이 곧 게임 호환성을 뜻하지 않습니다.

## 자주 묻는 질문

메뉴가 영어로 나온다면 Settings → Language를 선택하고 ui/lang/ 폴더를 완전히 설치했는지 확인하세요.

설정을 바꾼 뒤 게임이 실행되지 않으면 저장 데이터를 지우지 말고 해당 세션에서 **Safe Launch**를 사용해 보세요. [ZIP/FFPFSC 설치](../../INSTALL.md), [문제 해결](../../TROUBLESHOOTING.md), [지원](../../SUPPORT.md)을 참고하세요.

이 프로젝트는 게임, 콘솔 키, 펌웨어를 제공하지 않습니다. 공개 오류 보고서에 개인정보를 올리지 마세요.
