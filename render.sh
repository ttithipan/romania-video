#!/bin/sh
# render.sh — build the film whole, or one file per scene.
#
# Finished mp4s are written to ./output (silent in film_silent/ and scene_silent/,
# voiced in film_vo/ and scenes_vo/), which is tracked in git so a fresh clone
# already has the renders. Intermediates/partials stay in ./media.
#
#   ./render.sh                    whole film         -> output/film_silent/Film.mp4
#   ./render.sh scenes             one file per scene -> output/scene_silent/scene_NN_<scene>.mp4
#   ./render.sh sc_race sc_stop    only the named scenes
#
# Override the Manim quality (default -qh = 1080p60) or the destination:
#   QUALITY=-ql ./render.sh
#   OUT=/tmp/preview ./render.sh sc_route
#
# Requires the packages in requirements.txt (activate .venv first).
set -eu
cd "$(dirname "$0")"

if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python; fi
Q="${QUALITY:--qh}"
OUT="${OUT:-output}"
TMP=media/_render
mkdir -p "$OUT"

list_scenes() { "$PY" -c "import film; print(' '.join(film.ORDER))"; }
# 1-based position of a scene in film.ORDER (0 if unknown)
scene_index() { "$PY" -c "import film; o=film.ORDER; print(o.index('$1')+1 if '$1' in o else 0)"; }

if [ "${1:-all}" = "all" ]; then
  mkdir -p "$OUT/film_silent"
  "$PY" -m manim "$Q" --disable_caching --media_dir "$TMP" film.py Film
  cp "$(find "$TMP" -name 'Film.mp4' | head -n 1)" "$OUT/film_silent/Film.mp4"
  rm -rf "$TMP"
  echo "Whole film -> $OUT/film_silent/Film.mp4"
  exit 0
fi

# Per-scene mode: "scenes" (all) or an explicit list of scene names.
[ "${1:-}" = "scenes" ] && shift
# shellcheck disable=SC2086
LIST="${*:-$(list_scenes)}"

for s in $LIST; do
  echo "-- $s"
  SCENES="$s" "$PY" -m manim "$Q" --disable_caching --media_dir "$TMP" \
    film.py Film -o "$s" >/dev/null
  mkdir -p "$OUT/scene_silent"
  n="$(scene_index "$s")"
  if [ "$n" = 0 ]; then
    dest="$OUT/scene_silent/$s.mp4"          # not in ORDER: keep the bare name
  else
    dest="$(printf '%s/scene_silent/scene_%02d_%s.mp4' "$OUT" "$n" "$s")"
  fi
  cp "$(find "$TMP" -name "$s.mp4" | head -n 1)" "$dest"
done
rm -rf "$TMP"
echo "Scenes -> $OUT/scene_silent/scene_NN_<scene>.mp4"
