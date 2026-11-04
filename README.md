# FREQUENCY — GitHub Pages Music Studio

Open https://rugisa.github.io/MUSIC/ after the GitHub Pages deployment action succeeds.

## Features
- Instant original procedural music composition, no backend, login, API key or external assets
- 30-second loop, browser playback, stereo WAV download, prompt-guided style selection
- Natural-language revision keywords, version history, replay earlier versions

## Publishing
1. Upload `index.html`, `studio.js`, and `.github/workflows/pages.yml` at the repository root of `RUGISa/MUSIC` (`main` branch).
2. Open Settings → Pages → Build and deployment → Source → **GitHub Actions**.
3. In Actions, wait for **Deploy FREQUENCY to GitHub Pages** to complete.
4. Open https://rugisa.github.io/MUSIC/.

## Important limitations
This version is **not a text-to-audio AI model**. GitHub Pages does not run Python or GPU inference. It provides a usable, instant, fully client-side procedural synthesis alternative, including a simple keyword-driven revision workflow. It cannot guarantee the same quality as a professionally trained music model. No external samples or recordings are loaded. The code is original to this project, but copyright clearance or exclusive rights to the output are **not guaranteed**. For publication in a paid game, review the track for similarity and obtain legal advice when needed. Browsers may require a user click before audio playback.
