# Eden Encore — 설정 · 한국어

[개요](README.ko.md) · [설치 및 업데이트](INSTALL.ko.md) · [설정](SETTINGS.ko-KR.md) · [문제 해결](TROUBLESHOOTING.ko-KR.md) · [지원](SUPPORT.ko-KR.md) · [접근성](ACCESSIBILITY.ko-KR.md) · [🌐](../../LANGUAGES.md)

권장 시작 설정은 Vulkan, TV 출력 1440p, 게임 내부 배율 1.25x, 공간 업스케일링 FSR 1(선명도 50%), FXAA, 60 Hz입니다. TV 출력 해상도와 게임 내부 렌더링 해상도는 서로 다릅니다. 프레임 생성은 게임 시뮬레이션 속도 자체를 높이지 않습니다.

## Vulkan / FSR 1 — 설정

| `Minimum` | `Recommended` | `High` |
| --- | --- | --- |
| `Vulkan` · `1080p` · `1×` · `Bilinear` · `60 Hz` | `Vulkan` · `1440p` · `1.25×` · `FSR 1` · `FXAA` · `60 Hz` | `Vulkan` · `2160p` · `1.5×` · `Bicubic` · `FXAA` · `60 Hz` |

## 설정 · Touchpad

게임 중 Touchpad를 짧게 누르면 Encore 빠른 설정 메뉴가 열립니다. 중앙 시스템 버튼은 콘솔 전용입니다. 그래픽, 버튼 매핑, FPS, 진단 정보를 이 메뉴에서 확인할 수 있습니다. 일부 설정 변경은 게임을 다시 시작해야 적용됩니다. 언어는 Settings → Language에서 선택합니다. 메뉴에는 PS5 공식 시스템 언어 31개 항목만 표시됩니다.

## 접근성

큰 글씨, 높은 대비, 움직임 줄이기 옵션은 접근성 메뉴에서 각각 켤 수 있으며 기본적으로 모두 꺼져 있습니다. 런처의 접근성이 모든 게임 내부의 접근성을 보장하지는 않습니다.

## 문제 해결

실행되지 않으면 eboot.bin, sce_sys, ui/lang 위치를 확인하세요. 게임이 표시되지 않으면 선택한 저장소 루트의 roms 폴더를 확인합니다. 메뉴가 영어로만 나오면 번역 파일을 확인하세요. Safe Launch는 저장 데이터를 삭제하지 않고 개별 게임 설정을 복원합니다.

## 지원

GitHub Issues에 Encore 버전, PS5 펌웨어, 재현 절차, 관련 설정, 개인정보를 제거한 로그를 포함하세요. 키, 저장 파일, 개인 정보는 공개하지 마세요.

/data/prosperoeden/ 폴더를 삭제하지 마세요. 설정, 저장 데이터, 키가 들어 있을 수 있습니다. 외부 저장소도 백업하세요.

---

마지막으로 실제 컴파일된 공개 PS5 패키지는 2026년 10월 15일 버전입니다. 10월 30일 공개판은 복사본입니다. 새 사전 출시 초안에는 실행 파일이나 검증된 2세대 콘솔 게임 호환성이 포함되지 않습니다.

[English](../../SETTINGS.md) · [설치 및 업데이트](INSTALL.ko.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
