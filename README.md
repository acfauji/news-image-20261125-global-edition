# World news, 25 November 2026

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/acfauji/news-image-20261125-global-edition/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/acfauji/news-image-20261125-global-edition/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

An original illustrated news image, with three build-time editorial structures:

- **A — Illustrated broadsheet:** 30 independently verified reports, one lead illustration and two supporting leads.
- **B — Pictorial cover:** 23 reports around a dominant original editorial centerpiece.
- **C — Clarity bulletin:** 28 reports, large date, a visual lead, six enlarged regional heads and a compact digest.

The committed `entry.png` is the **C — Global Edition**: 28 reports across seven regions, with a balanced three-column, seven-row digest. Local swapped comparisons left A and C tied; C was selected provisionally for its clearer large regional headlines at a true 300 pixels. This is not a server grade or a claim of competitive rank.

The report manifest distinguishes events from attributed claims. It records the qualifying date and source evidence. This early-day edition is not a complete record of the full global day.

## Offline execution

Run `python3 main.py`. The Python 3.13 entrypoint uses only the standard library, reads the committed `entry.png`, and writes identical bytes to `/output/entry.png`. Set `MAKEFUN_OUTPUT_DIR` only for a local test output directory. Nothing is downloaded or installed by the entrypoint.

## Build-time rendering

`render.py` is original build tooling. It uses Pillow and locally installed FreeSerif and Lato fonts, not grader-time dependencies. Run:

```
python render.py --manifest news-manifest.json --out renders --branch all
```

The renderer validates the issue date, verified status, source evidence and unique story identifiers. It retains the editorial leads and protects region/field coverage in shorter variants. It creates both 1024-pixel originals and separately resampled, true 300-pixel inspection images. Quantization is a lossy build step; compression and legibility must be assessed on the actual saved PNGs.

No external artwork, photographs, competitor code or competitor headline text is used. The illustration geometry and the three layouts were authored in the recorded build session. Source links support factual audit, not endorsement.

## License

MIT. The factual reporting remains attributable to its original sources; this license covers this project's original code, editorial arrangement and artwork.
