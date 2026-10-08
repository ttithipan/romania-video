#!/bin/sh
# Render the seven guide GIFs for the romania-web guide sidebar.
#
# GIFs are written to ./output/gifs, which is tracked in git so a fresh clone
# already has them. Manim intermediates and the palette temp file stay in the
# gitignored ./media.
#
# Each scene is rendered at 720x460, 13 fps (2x the sidebar's display size),
# then encoded to a looping GIF with an ffmpeg palette pass. Playback is slowed
# by SLOW (playback speed = 1/SLOW). The scenes live in gifs.py.
#
# Publish a copy into the site's public folder (romania-web is its own repo, so
# this is opt-in):
#   PUBLISH=1 ./render_gifs.sh
# Render somewhere else:
#   OUT=/tmp/gifs ./render_gifs.sh
#
# Requires the packages in requirements.txt (activate .venv first) and ffmpeg.
set -eu
cd "$(dirname "$0")"

OUT="${OUT:-output/gifs}"
WEB="${WEB:-../romania-web/public/gifs}"
PUBLISH="${PUBLISH:-0}"
TMP="media/.gif_palette"
FPS=13
SLOW=2.5
mkdir -p "$OUT" "$TMP"

# scene:output-file pairs
PAIRS="
UCSRings:ucs-cost-rings.gif
AStarVsUCS:astar-vs-ucs.gif
AdmissibleConsistent:admissible-consistent.gif
LPVectorDecomposition:lp-vector-decomposition.gif
ALTTriangleInequality:alt-triangle-inequality.gif
EnsembleMax:ensemble-max.gif
EnsemblePerformance:ensemble-performance.gif
"

render_one() {
  scene="$1"; out="$2"
  echo "-- $scene -> $OUT/$out"
  .venv/bin/manim render -r 720,460 --fps "$FPS" --format mp4 "gifs.py" "$scene" >/dev/null
  mp4="media/videos/gifs/460p${FPS}/${scene}.mp4"
  pal="$TMP/${scene}.png"
  ffmpeg -y -v error -i "$mp4" -vf "setpts=PTS*${SLOW},fps=${FPS},palettegen=max_colors=32:stats_mode=full" "$pal"
  ffmpeg -y -v error -i "$mp4" -i "$pal" \
    -lavfi "setpts=PTS*${SLOW},fps=${FPS},scale=720:460:flags=lanczos[x];[x][1:v]paletteuse=dither=none:diff_mode=rectangle" \
    -loop 0 "$OUT/$out"
}

echo "$PAIRS" | while IFS=: read -r scene out; do
  [ -z "$scene" ] && continue
  render_one "$scene" "$out"
done

rm -rf "$TMP"
echo "GIFs -> $OUT/"

if [ "$PUBLISH" = "1" ]; then
  mkdir -p "$WEB"
  cp "$OUT"/*.gif "$WEB"/
  echo "Published -> $WEB/"
fi
