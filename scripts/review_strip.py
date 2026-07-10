#!/usr/bin/env python3
"""Собрать раскадровку всех сгенерённых сцен в один обзор и открыть в snip."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "public" / "scroll" / "raw"
ORDER = ["forest", "gate", "alley", "house", "interior", "garden"]


def strip(mp4: Path, dst: Path, n=4):
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
        capture_output=True, text=True).stdout.strip())
    total = int(dur * 30)
    idx = [min(total - 1, int(total * k / (n - 1))) for k in range(n)]
    sel = "+".join(f"eq(n\\,{x})" for x in idx)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4),
                    "-vf", f"select='{sel}',scale=320:180,tile={n}x1", "-frames:v", "1", str(dst)], check=True)


def main():
    strips = []
    for sid in ORDER:
        f = RAW / f"{sid}.mp4"
        if f.exists():
            d = Path(f"/tmp/scene_{sid}.jpg")
            strip(f, d)
            strips.append((sid, d))
    if not strips:
        print("нет клипов"); return
    inputs = []
    for _, d in strips:
        inputs += ["-i", str(d)]
    fc = "".join(f"[{i}:v]scale=1280:-1[s{i}];" for i in range(len(strips)))
    fc += "".join(f"[s{i}]" for i in range(len(strips))) + f"vstack={len(strips)}"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
                    "-filter_complex", fc, "/tmp/scenes_overview.jpg"], check=True)
    print("labels top->bottom:", ", ".join(s for s, _ in strips))
    print("overview: /tmp/scenes_overview.jpg")


if __name__ == "__main__":
    main()
