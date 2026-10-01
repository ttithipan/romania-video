#!/bin/sh
# Self-contained render of the PathfindingFilm scene (28 chapters, ~10 min).
# Requires the packages in requirements.txt. Only film.py, storyboard.py and
# project_data.json are needed — no export step, no ../main dependency.
set -eu
cd "$(dirname "$0")"
python -m manim -qh --disable_caching film.py PathfindingFilm
