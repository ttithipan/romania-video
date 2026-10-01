# Pathfinding video (Manim source)

Self-contained Manim source for the ~10 minute explainer that accompanies the
Romania pathfinding visualizer. 28 chapters: a journey, uniform cost search,
A*, the LP and landmark lower bounds, the combined estimate `h = max(hLP, hALT)`,
a proof block that measures the heuristic on every pair, then bidirectional A*.

## Files

| File | Role |
|------|------|
| `film.py` | `PathfindingFilm` scene and `RoadMap` — all animations |
| `storyboard.py` | `CHAPTERS`: title, question, beats, narration for each chapter |
| `manim.cfg` | Manim CLI config (1080p, media dir) |
| `project_data.json` | Graph, distances and exported algorithm traces the film draws |
| `narration.md` | Speaker notes / human narrator script |
| `render.sh` | Renders the scene to `media/videos/film/1080p60/PathfindingFilm.mp4` |
| `requirements.txt` | Runtime dependencies |

## Render

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
./render.sh
```

Preview a subset instead of the whole film (zero-based chapter indices):

```sh
CHAPTER_SELECTION=13,14 .venv/bin/python -m manim -ql film.py PathfindingFilm
```

`project_data.json` is exported from the main app (`../main`) so the film's
numbers come from the same algorithms the site runs; it is checked into this
folder, so no rebuild is required to render.
