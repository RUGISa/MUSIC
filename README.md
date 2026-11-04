# FREQUENCY — Musical Composition v3

GitHub Pages deployable browser-only 30-second instrumental BGM composer.

## Features
- Five distinct arrangements: band, orchestra, acoustic, piano, jazz.
- Six game scenes.
- Deterministic melody motifs, chord progressions, bass lines, rhythmic phrasing, dynamic sections, note rests and variation.
- Instruments synthesized directly in code. No soundfont, existing music, licensed recording, API key, Python server, or external dependencies.
- Revision history and 30-second stereo WAV export.

## Deploy
Upload the files at the root of the `main` branch. In Settings > Pages choose GitHub Actions. The supplied `.github/workflows/pages.yml` deploys the root folder.

## Limitations
This is procedural composition with approximate synthesized acoustic timbres, NOT an AI-generated studio recording. It does not provide realistic sampled orchestral strings or guitar playing. Commercial-use suitability and similarity to existing works still require review.
