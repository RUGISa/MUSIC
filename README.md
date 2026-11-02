# FREQUENCY — GitHub Pages 배포 + Mac 로컬 AI

## GitHub Actions 배포 (RUGISa/MUSIC)

`main` 브랜치에 `public/` 또는 `.github/workflows/pages.yml` 변경사항을 푸시하면 **pages build and deployment** 액션이 실행돼 https://rugisa.github.io/MUSIC/ 를 업데이트합니다. GitHub 저장소 Settings → Pages → Build and deployment → **Source: GitHub Actions** 로 선택해 주세요. Actions 탭에서 `pages build and deployment`를 선택하고 **Run workflow**로 수동 실행도 가능합니다.

**중요**: GitHub Pages는 정적 호스팅입니다. 이 주소에서 ACE-Step 모델이나 로컬 Python 서버가 실행되지는 않습니다. Pages에는 다운로드/안내 화면을 배포하고, Mac 음악 생성은 `START_WEBSITE.command`를 실행해 `http://127.0.0.1:8765`에서 사용합니다.

## Mac 실행

GitHub 저장소를 내려받아 압축 해제 → `START_WEBSITE.command` 더블클릭. Python 3 및 초기 모델 다운로드가 필요합니다. 연결 실패 시 `~/Library/Application Support/FREQUENCY/` 로그를 확인하세요.

## 기존 설명

# FREQUENCY — Mac local AI music studio

A lightweight localhost web UI for ACE-Step 1.5, with a 10-second AI sketch, 30-second repeating WAV, and quick tonal edits. **GitHub Pages cannot execute AI models or local Python servers.** Clone/download this repository and open `START_WEBSITE.command` on your Mac.

## Start

1. Download this repository (Code → Download ZIP) and extract it, or clone it with Git.
2. On Apple Silicon macOS, double-click `START_WEBSITE.command`, or run `bash START_WEBSITE.command` in Terminal.
3. The browser opens automatically at `http://127.0.0.1:8765` (or another available port).
4. First run installs ACE-Step dependencies and fetches the main model. **Internet and sufficient free disk space are required.** This is not instantaneous: the model is large. The site displays an installation phase and errors.
5. On later runs, already-downloaded resources are reused.

## How auto connection works

- Runs the local web UI immediately, without starting a native desktop app.
- Reuses a working local ACE-Step API on `127.0.0.1:8001` where available.
- Fetches ACE-Step source from `https://github.com/ace-step/ACE-Step-1.5` into `~/Library/Application Support/FREQUENCY/ACE-Step-1.5` when missing.
- Installs `uv` via its official installer if missing; `uv sync` installs dependencies.
- Attempts model download via Hugging Face, then ModelScope if the first fails.
- Launches the official `start_api_server_macos.sh` when the API is not already running.
- If download fails, the site shows an error instead of claiming a successful connection.
- Logs: `~/Library/Application Support/FREQUENCY/frequency-web.log` and `ace-step.log`.

## Requirements / limitations

- Apple Silicon Mac (including ARM64 MacBook Neo); native Python 3, Git, sufficient disk and memory.
- 8GB MacBook Neo has significant memory and inference constraints; a 10-second draft may still take a long time or fail. Looping to 30 seconds **does not** mean 30 seconds of unique music.
- The currently installed backend may use different model paths or API versions, and compatibility is not guaranteed. Check backend logs on mismatch.
- This code **cannot** guarantee a finished game-quality track or immediate generation. ACE-Step model download is a real prerequisite.
- All services bind to localhost; don't expose port 8001/8765 publicly.
- ACE-Step is third-party software; review its licensing and terms separately before commercial use.

## Version notes

The starter uses the existing FREQUENCY iterative interface and proxy. Raw AI music can be edited without model inference for tone/level changes only. Melody/instrumentation changes require new AI inference.
