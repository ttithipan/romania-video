#!/usr/bin/env python3
"""Build vo_timing.json from the cleaned voiceover clips.

Maps each film scene to the spoken duration of each of its beats, so film.py can
hold every subtitle block for exactly as long as its voiceover line lasts.

    python build_vo_timing.py            # reads audio/raw + audio/clean
"""
import json
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / 'audio'
MANIFEST = AUDIO / 'raw' / 'manifest.json'
CLEAN = AUDIO / 'clean'
OUT = ROOT / 'vo_timing.json'
TAIL = 0.30   # silence kept after a line's speech before the next beat


def main() -> int:
    man = json.loads(MANIFEST.read_text())
    scenes: dict[str, list[float]] = {}
    missing = []
    for c in man['clips']:
        wav = CLEAN / (Path(c['file']).stem + '.wav')
        if not wav.exists():
            missing.append(str(wav))
            continue
        with wave.open(str(wav)) as w:
            dur = w.getnframes() / w.getframerate()
        scenes.setdefault(c['scene'], []).append(round(dur, 3))

    if missing:
        print(f'warning: {len(missing)} cleaned clips missing, e.g. {missing[0]}',
              file=sys.stderr)

    data = {'source': str(CLEAN.relative_to(ROOT)), 'tail': TAIL,
            'total_s': round(sum(d for v in scenes.values() for d in v), 2),
            'scenes': scenes}
    OUT.write_text(json.dumps(data, indent=2) + '\n')

    for sc, durs in scenes.items():
        print(f'  {sc:16s} {len(durs):2d} beats  {sum(durs):6.2f}s')
    print(f'wrote {OUT}  ({len(scenes)} scenes, '
          f'{sum(len(v) for v in scenes.values())} beats, {data["total_s"]}s speech)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
