# Eden Encore — 설정 · 한국어

[개요](README.ko.md) · [설치 및 업데이트](INSTALL.ko-KR.md) · [설정](SETTINGS.ko-KR.md) · [문제 해결](TROUBLESHOOTING.ko-KR.md) · [지원](SUPPORT.ko-KR.md) · [접근성](ACCESSIBILITY.ko-KR.md) · [Languages](../../LANGUAGES.md)

권장 시작 설정은 Vulkan, TV 출력 1440p, 게임 내부 배율 1.25x, 공간 업스케일링 FSR 1(선명도 50%), FXAA, 60 Hz입니다. TV 출력 해상도와 게임 내부 렌더링 해상도는 서로 다릅니다. 프레임 생성은 게임 시뮬레이션 속도 자체를 높이지 않습니다.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** 권장 시작 설정은 Vulkan, TV 출력 1440p, 게임 내부 배율 1.25x, 공간 업스케일링 FSR 1(선명도 50%), FXAA, 60 Hz입니다. TV 출력 해상도와 게임 내부 렌더링 해상도는 서로 다릅니다. 프레임 생성은 게임 시뮬레이션 속도 자체를 높이지 않습니다.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## 접근성

큰 글씨, 높은 대비, 움직임 줄이기 옵션은 접근성 메뉴에서 각각 켤 수 있으며 기본적으로 모두 꺼져 있습니다. 런처의 접근성이 모든 게임 내부의 접근성을 보장하지는 않습니다.

## 문제 해결

실행되지 않으면 eboot.bin, sce_sys, ui/lang 위치를 확인하세요. 게임이 표시되지 않으면 선택한 저장소 루트의 roms 폴더를 확인합니다. 메뉴가 영어로만 나오면 번역 파일을 확인하세요. Safe Launch는 저장 데이터를 삭제하지 않고 개별 게임 설정을 복원합니다.

/data/prosperoeden/ 폴더를 삭제하지 마세요. 설정, 저장 데이터, 키가 들어 있을 수 있습니다. 외부 저장소도 백업하세요.

---

마지막으로 실제 컴파일된 공개 PS5 패키지는 2026년 10월 15일 버전입니다. 10월 30일 공개판은 복사본입니다. 새 사전 출시 초안에는 실행 파일이나 검증된 2세대 콘솔 게임 호환성이 포함되지 않습니다.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)