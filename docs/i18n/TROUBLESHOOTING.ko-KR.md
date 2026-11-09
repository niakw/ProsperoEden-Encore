# Eden Encore — 문제 해결 · 한국어

[개요](README.ko.md) · [설치 및 업데이트](INSTALL.ko-KR.md) · [설정](SETTINGS.ko-KR.md) · [문제 해결](TROUBLESHOOTING.ko-KR.md) · [지원](SUPPORT.ko-KR.md) · [접근성](ACCESSIBILITY.ko-KR.md) · [Languages](../../LANGUAGES.md)

실행되지 않으면 eboot.bin, sce_sys, ui/lang 위치를 확인하세요. 게임이 표시되지 않으면 선택한 저장소 루트의 roms 폴더를 확인합니다. 메뉴가 영어로만 나오면 번역 파일을 확인하세요. Safe Launch는 저장 데이터를 삭제하지 않고 개별 게임 설정을 복원합니다.

## 설치 및 업데이트

Releases에서 실제로 공개된 패키지를 다운로드하고 앱과 데이터를 먼저 백업하세요. ZIP/FTP 설치는 PPSA99008 폴더 전체를 /data/homebrew/PPSA99008/에 복사합니다. FFPFSC/ShadowMountPlus 방식과 혼용하지 말고 제공된 SHA-256을 검증하세요.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## 설정

권장 시작 설정은 Vulkan, TV 출력 1440p, 게임 내부 배율 1.25x, 공간 업스케일링 FSR 1(선명도 50%), FXAA, 60 Hz입니다. TV 출력 해상도와 게임 내부 렌더링 해상도는 서로 다릅니다. 프레임 생성은 게임 시뮬레이션 속도 자체를 높이지 않습니다.

## 지원

GitHub Issues에 Encore 버전, PS5 펌웨어, 재현 절차, 관련 설정, 개인정보를 제거한 로그를 포함하세요. 키, 저장 파일, 개인 정보는 공개하지 마세요.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

/data/prosperoeden/ 폴더를 삭제하지 마세요. 설정, 저장 데이터, 키가 들어 있을 수 있습니다. 외부 저장소도 백업하세요.

---

마지막으로 실제 컴파일된 공개 PS5 패키지는 2026년 10월 15일 버전입니다. 10월 30일 공개판은 복사본입니다. 새 사전 출시 초안에는 실행 파일이나 검증된 2세대 콘솔 게임 호환성이 포함되지 않습니다.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)