# Romania pathfinding — explainer film (Manim source)

The silent, subtitle-driven explainer that accompanies the Romania pathfinding
visualizer. **22 scenes, ~7¼ min**, styled after 3Blue1Brown: it walks from
"which route is cheapest?" through uniform-cost search, A*, the LP and landmark
lower bounds, `h = max(hLP, hALT)`, the optimality proofs, bidirectional search,
and a code section that reads the real implementation.

Subtitles are the only narration (a human voiceover will replace them later), and
each subtitle is paired with the graphic that is on screen in the same beat.

## Files

| File | Role |
|------|------|
| `film.py` | **The film.** `Film` scene (22 scenes in `ORDER`), subtitles in `beat(...)`, plus the layout auditor |
| `scene_kit.py` | Shared building blocks: `project_data.json` load, palette, `label()`, `RoadMap` |
| `gifs.py` | Seven short looping scenes for the web guide sidebar (separate tool, below) |
| `manim.cfg` | Manim CLI defaults (1080p, media dir) |
| `project_data.json` | Graph, distances and exported algorithm traces the film draws |
| `render.sh` | Renders the whole film, or one file per scene, into `output/` |
| `render_vo.sh` | Renders the voiceover-muxed versions into `output/film_vo/` and `output/scenes_vo/` |
| `build_vo_timing.py` | Builds `vo_timing.json` (per-beat spoken durations) from `audio/blocks/clean` |
| `fit_vo_anim.py` | Builds `vo_anim.json` (per-beat animation speed-up factors) with a two-pass fit |
| `build_vo_track.py` | Assembles a voiceover track from the clips + a beat schedule (`VO_SCHEDULE`) |
| `audio/` | Voiceover: `VO-AI_draft.mp3` + `raw/` (uncleaned per-block clips, `manifest.json`) + `clean/` (denoised + trimmed) |
| `output/` | **Rendered results (tracked in git):** silent `film/`, `scenes/`, `gifs/`; voiced `film_vo/`, `scenes_vo/` |
| `render_gifs.sh` | Renders the seven guide GIFs into `output/gifs/` (`PUBLISH=1` copies them into the site) |
| `requirements.txt` | Runtime dependencies |

> The older 28-chapter *voiced* film and its `storyboard.py` / `narration.md` /
> `timeline*.json` have been removed from the working tree; they remain available
> in git history. There is one film file, `film.py` — earlier iterations live in
> the commit log rather than in suffixed filenames.

## Render

Finished mp4s are written to **`output/`** (silent in `film/` and `scenes/`,
voiced in `film_vo/` and `scenes_vo/`), which is committed so a fresh clone
already has the renders and does not need to rebuild. Intermediates and partial
frame files stay in the gitignored `media/`.

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

./render.sh                 # whole film        -> output/film_silent/Film.mp4
./render.sh scenes          # one file per scene -> output/scene_silent/scene_01_sc_route.mp4 ...
./render.sh sc_race sc_stop # a few scenes only

QUALITY=-ql ./render.sh     # fast 480p15 pass
OUT=/tmp/preview ./render.sh sc_route   # write somewhere else
```

Silent and voiced renders are kept side by side:

| Folder | Contents |
|--------|----------|
| `output/film_silent/` | silent whole film — `Film.mp4` |
| `output/scene_silent/` | silent per-scene — `scene_NN_<scene>.mp4` |
| `output/film_vo/` | voiced whole film — `Film.mp4` |
| `output/scenes_vo/` | voiced per-scene — `scene_NN_<scene>_vo.mp4` |
| `output/gifs/` | guide GIFs |
| `output/samples/` | scratch review frames/clips (gitignored) |

Per-scene files are `scene_NN_<scene>.mp4`, where `NN` is the scene's 1-based
position in `film.ORDER` (so they sort in playback order). The `<scene>` part is
the scene method, e.g. `scene_01_sc_route.mp4`, `scene_11_sc_lpproof.mp4`,
`scene_14_sc_code_astar.mp4`, `scene_22_sc_recap.mp4`.

## Voiceover render

The voiced film needs the per-beat timing (`vo_timing.json`) and the animation
speed-up fit (`vo_anim.json`), both derived from the cleaned clips in
`audio/clean`:

```sh
.venv/bin/python build_vo_timing.py            # spoken durations -> vo_timing.json
# refresh the fit (two-pass) whenever the visuals change:
VO_SCHEDULE=media/_fit/p1.json .venv/bin/python -m manim -ql film.py Film
.venv/bin/python fit_vo_anim.py media/_fit/p1.json
VO_SCHEDULE=media/_fit/p2.json .venv/bin/python -m manim -ql film.py Film
.venv/bin/python fit_vo_anim.py media/_fit/p1.json media/_fit/p2.json

./render_vo.sh              # whole film + every scene -> output/film_vo, output/scenes_vo
./render_vo.sh film         # whole film only
./render_vo.sh scenes       # every scene
./render_vo.sh sc_race      # named scenes only
QUALITY=-ql ./render_vo.sh sc_recap   # fast preview
```

## Reviewing a scene

Render a subset at low quality:

```sh
SCENES=sc_lpproof,sc_code_astar .venv/bin/python -m manim -ql film.py Film
```

Run the **layout auditor** — it checks, on every settled frame, for text that
overlaps a graphic and for the mascot overlapping anything:

```sh
AUDIT=1 .venv/bin/python -m manim -ql film.py Film
```

## Guide GIFs (web sidebar — separate tool)

The seven animations the `romania-web` sidebar asks for are built by `gifs.py`
and written to **`output/gifs/`** (tracked, so a clone already has them):

| Scene | Output |
|-------|--------|
| `UCSRings` | `output/gifs/ucs-cost-rings.gif` |
| `AStarVsUCS` | `output/gifs/astar-vs-ucs.gif` |
| `AdmissibleConsistent` | `output/gifs/admissible-consistent.gif` |
| `LPVectorDecomposition` | `output/gifs/lp-vector-decomposition.gif` |
| `ALTTriangleInequality` | `output/gifs/alt-triangle-inequality.gif` |
| `EnsembleMax` | `output/gifs/ensemble-max.gif` |
| `EnsemblePerformance` | `output/gifs/ensemble-performance.gif` |

Each is 720x460, 13 fps, loops forever, and reuses the same
`project_data.json` numbers as the film. The site consumes them from
`romania-web/public/gifs/` (`Guide.tsx` → `/gifs/<name>.gif`); since
`romania-web` is its own repo, publishing there is a separate, opt-in step:

```sh
./render_gifs.sh            # -> output/gifs/
PUBLISH=1 ./render_gifs.sh  # also copy into ../romania-web/public/gifs/
```

`project_data.json` is exported from the main app (`../main`), so the film's
numbers come from the same algorithms the site runs; it is checked in, so no
rebuild is required to render.
