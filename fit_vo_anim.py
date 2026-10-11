#!/usr/bin/env python3
"""Compute per-beat animation speed factors so each beat fits its voiceover line.

Reads one or two *timing-pass* schedules produced by film.py (VO_SCHEDULE). Each
schedule records, per beat, the fixed `overhead` (subtitle fade + beat pause) and
the animation's length `fn` for the speed factor that was active.

With a single schedule we approximate scale = budget / fn. With two (the first
unscaled, the second at known factors) we solve the exact linear relation
fn(scale) = a + b*scale per beat, then pick the scale that makes
overhead + fn == audio + TAIL. That removes the residual overrun.

    python fit_vo_anim.py /tmp/p1.json                 # from the unscaled pass
    python fit_vo_anim.py /tmp/p1.json /tmp/p2.json    # refine using a scaled pass
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VO_TAIL = 0.30
MIN_SCALE = 0.30
ANIM = ROOT / 'vo_anim.json'


def load(path):
    return {(e['scene'], e['beat']): e for e in json.loads(Path(path).read_text())}


def main() -> int:
    if len(sys.argv) not in (2, 3):
        raise SystemExit('usage: fit_vo_anim.py <unscaled.json> [<scaled.json>]')
    p1 = load(sys.argv[1])
    p2 = load(sys.argv[2]) if len(sys.argv) == 3 else None
    prev = json.loads(ANIM.read_text())['scenes'] if ANIM.exists() else None

    scenes: dict[str, list[float]] = {}
    sped = 0
    for (scene, beat), e in sorted(p1.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        budget = e['audio'] + VO_TAIL - e['overhead']
        fn1 = e['fn']

        s_prev = 1.0
        if prev is not None:
            lst = prev.get(scene, [])
            if beat - 1 < len(lst):
                s_prev = lst[beat - 1]

        scale = 1.0
        if fn1 > 0.01:
            if p2 is not None and (scene, beat) in p2 and s_prev < 0.999:
                fn2 = p2[(scene, beat)]['fn']
                b = (fn2 - fn1) / (s_prev - 1.0)      # fn = a + b*scale
                a = fn1 - b
                scale = (budget - a) / b if b > 1e-3 else budget / fn1
            else:
                scale = budget / fn1
            scale = round(min(1.0, max(MIN_SCALE, scale)), 4)

        scenes.setdefault(scene, []).append(scale)
        if scale < 0.999:
            sped += 1
            print(f"  {scene:16s} beat {beat}: budget {budget:5.2f}s -> x{1/scale:.2f}"
                  + ('  (capped)' if scale <= MIN_SCALE + 1e-9 else ''))

    ANIM.write_text(json.dumps({'tail': VO_TAIL, 'min_scale': MIN_SCALE, 'scenes': scenes},
                               indent=2) + '\n')
    print(f'wrote {ANIM}  ({sped} beats sped up)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
