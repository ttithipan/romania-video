#!/usr/bin/env python3
"""Assemble a voiceover track for a render from the cleaned clips and the beat
schedule produced by film.py (VO_SCHEDULE).

Each clip is placed at its beat's recorded start time, so the track is sample
aligned with the video. The 300 ms inter-line spacing comes from the beat
timing (VO_TAIL), not from padding here.

    python build_vo_track.py \
        --schedule /tmp/sched_route.json \
        --clips audio/blocks/clean \
        --manifest audio/blocks/manifest.json \
        --duration 22.07 --out /tmp/vo_route.wav
"""
import argparse
import json
import wave
from pathlib import Path

import numpy as np


def read_wav(path: Path) -> tuple[np.ndarray, int, int]:
    with wave.open(str(path)) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if sw != 2:
        raise SystemExit(f"{path}: expected 16-bit PCM")
    a = np.frombuffer(raw, "<i2").reshape(-1, ch).astype(np.float32) / 32768.0
    return a, sr, ch


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--schedule", required=True, type=Path)
    ap.add_argument("--clips", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--duration", type=float, required=True, help="track length (s)")
    ap.add_argument("--sample-rate", type=int, default=48000)
    ap.add_argument("--gain", type=float, default=1.0)
    args = ap.parse_args()

    sched = json.loads(args.schedule.read_text())
    man = json.loads(args.manifest.read_text())
    stem = {(c["scene"], c["beat"]): Path(c["file"]).stem for c in man["clips"]}

    sr = args.sample_rate
    n = int(round(args.duration * sr))
    out = np.zeros((n, 2), dtype=np.float32)

    for e in sched:
        key = (e["scene"], e["beat"])
        if key not in stem:
            print(f"  (no clip for {key})")
            continue
        clip, sr_c, ch = read_wav(args.clips / (stem[key] + ".wav"))
        if sr_c != sr:
            raise SystemExit(f"{key}: {sr_c} Hz != {sr} Hz")
        if ch == 1:
            clip = np.repeat(clip, 2, axis=1)
        i0 = int(round(e["start"] * sr))
        i1 = min(n, i0 + len(clip))
        out[i0:i1] += clip[: i1 - i0]

    peak = float(np.max(np.abs(out)))
    if peak > 1.0:
        print(f"  peak {20*np.log10(peak):.1f} dBFS, scaling to 0 dBFS")
        out /= peak
    pcm = (np.clip(out * args.gain, -1.0, 1.0) * 32767).astype("<i2")

    with wave.open(str(args.out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())

    print(f"wrote {args.out}  {len(out)/sr:.2f}s  peak "
          f"{20*np.log10(peak + 1e-9):.1f} dBFS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
