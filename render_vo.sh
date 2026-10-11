#!/bin/sh
# render_vo.sh — render the voiceover-muxed versions.
#
#   ./render_vo.sh                     whole film + every scene
#   ./render_vo.sh film                whole film only
#   ./render_vo.sh scenes              every scene
#   ./render_vo.sh sc_race sc_stop     only the named scenes
#
# Results:
#   whole film          -> output/film_vo/Film.mp4
#   one file per scene  -> output/scenes_vo/scene_NN_<scene>_vo.mp4
#
# The silent counterparts live in output/film_silent and output/scene_silent (render.sh).
#
# Timing comes from the voiceover: film.py holds each beat for its spoken length
# (vo_timing.json) and speeds each beat's animation up to fit (vo_anim.json).
# Refresh those when the visuals or the clips change:
#   .venv/bin/python build_vo_timing.py                       # -> vo_timing.json
#   VO_SCHEDULE=media/_fit/p1.json .venv/bin/python -m manim -ql film.py Film
#   .venv/bin/python fit_vo_anim.py media/_fit/p1.json
#   VO_SCHEDULE=media/_fit/p2.json .venv/bin/python -m manim -ql film.py Film
#   .venv/bin/python fit_vo_anim.py media/_fit/p1.json media/_fit/p2.json
#
# Requires ffmpeg and the cleaned clips in audio/clean.
set -eu
cd "$(dirname "$0")"

if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python; fi
Q="${QUALITY:--qh}"
TMP=media/_render_vo
CLIPS="${CLIPS:-audio/clean}"
MANIFEST="${MANIFEST:-audio/raw/manifest.json}"
mkdir -p "$TMP" output/film_vo output/scenes_vo

list_scenes() { "$PY" -c "import film; print(' '.join(film.ORDER))"; }
scene_index() { "$PY" -c "import film; o=film.ORDER; print(o.index('$1')+1 if '$1' in o else 0)"; }

# mux <schedule.json> <silent.mp4> <out.mp4>
mux() {
  dur="$(ffprobe -v error -show_entries format=duration \
         -of default=noprint_wrappers=1:nokey=1 "$2")"
  "$PY" build_vo_track.py --schedule "$1" --clips "$CLIPS" --manifest "$MANIFEST" \
      --duration "$dur" --out "$TMP/vo.wav" >/dev/null
  ffmpeg -y -v error -i "$2" -i "$TMP/vo.wav" \
      -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest "$3"
  echo "-> $3"
}

render_film() {
  VO_SCHEDULE="$TMP/film.json" "$PY" -m manim "$Q" --disable_caching \
      --media_dir "$TMP" film.py Film
  mux "$TMP/film.json" "$(find "$TMP" -name 'Film.mp4' | head -n 1)" \
      output/film_vo/Film.mp4
}

render_scene() {
  s="$1"
  SCENES="$s" VO_SCHEDULE="$TMP/$s.json" "$PY" -m manim "$Q" --disable_caching \
      --media_dir "$TMP" film.py Film -o "$s" >/dev/null
  n="$(scene_index "$s")"
  if [ "$n" = 0 ]; then
    out="output/scenes_vo/${s}_vo.mp4"
  else
    out="$(printf 'output/scenes_vo/scene_%02d_%s_vo.mp4' "$n" "$s")"
  fi
  mux "$TMP/$s.json" "$(find "$TMP" -name "$s.mp4" | head -n 1)" "$out"
}

case "${1:-all}" in
  film)   render_film ;;
  scenes) shift; for s in $(list_scenes); do render_scene "$s"; done ;;
  all)    render_film; for s in $(list_scenes); do render_scene "$s"; done ;;
  *)      for s in "$@"; do render_scene "$s"; done ;;
esac

rm -rf "$TMP"
echo "Voiced renders -> output/film_vo, output/scenes_vo"
