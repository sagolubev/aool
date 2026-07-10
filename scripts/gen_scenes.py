#!/usr/bin/env python3
"""Генерация 6 leg-клипов лендинга АУЛ (scroll-world Architecture A) на Sora-2.

Цепочка forward-take: forest -> gate -> alley -> house -> interior -> garden.
Каждый chain-leg сидируется реальным последним кадром предыдущего; house — из
реального рендера Дома "Вода" с сайта; forest — t2v. Строго последовательно.

Запуск: python3 scripts/gen_scenes.py [start_index]
  start_index — с какой сцены продолжить (0..5), для докатки после сбоя.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spike"))
from sora_lib import STYLE, create_video, poll_video, download_video, gen_image  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "public" / "scroll" / "raw"
SEED = ROOT / "spike" / "ref"          # сюда кладём seed-кадры
VODA = SEED / "voda_1280.png"          # реальный рендер дома (уже скачан в спайке)


def last_frame(mp4: Path, dst: Path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(mp4)],
        capture_output=True, text=True).stdout.strip()
    n = int(out)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4),
                    "-vf", f"select=eq(n\\,{n-1})", "-frames:v", "1", str(dst)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(dst), "-vf",
                    "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
                    str(dst)], check=True)


# (id, kind, prompt, seconds)
SCENES = [
    ("forest", "t2v",
     "Aerial drift over a serene birch-and-pine forest 25 km from the city, morning "
     "mist between the trees, a winding road leading toward a premium gated countryside "
     "village in the distance. Calm and inviting. End settling into a slow steady forward glide.", "8"),
    ("gate", "chain",
     "Continue the same slow steady forward drift, arriving at the village entrance: a "
     "stone stele 'Rodnaya Zemlya', a clean modern gatehouse, an avenue of trees "
     "beginning. Keep gliding forward, never pulling back.", "8"),
    ("alley", "chain",
     "Continue gliding forward down the central landscaped alley of the village: "
     "manicured greenery, an amphitheatre, a calm pond, wide walking paths, 25 hectares "
     "of parkland. End settling forward toward a modern house in the distance.", "8"),
    ("house", "anchor",
     "Slow cinematic camera gliding down and forward toward this modern two-storey house "
     "by the water at golden hour, warm interior lights switching on, subtle parallax. "
     "Preserve the exact architecture, glazing and materials of the reference. End "
     "settling as it drifts toward the floor-to-ceiling glass facade.", "8"),
    ("interior", "chain",
     "Continue forward, passing seamlessly through the floor-to-ceiling glass into a "
     "bright double-height living room: a designer boucle sofa, a stone-clad fireplace, "
     "wide oak floors, an open kitchen with a large marble island, a minimalist dining "
     "area with statement pendant lights, soft linen curtains. Keep gliding forward.", "8"),
    ("garden", "chain",
     "Continue gliding forward out onto the terrace and garden: a BBQ zone, fruit trees, "
     "a calm water view, warm sunset light. End settling to a gentle stop.", "8"),
]


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    RAW.mkdir(parents=True, exist_ok=True)
    for i, (sid, kind, prompt, secs) in enumerate(SCENES):
        if i < start:
            continue
        full = f"{STYLE} {prompt}"
        ref = None
        if kind == "anchor":
            ref = VODA
        elif kind == "chain":
            ref = SEED / f"{sid}_seed.png"
            if not ref.exists():
                raise SystemExit(f"нет seed {ref} — сгенерируй предыдущую сцену (запусти с index {i-1})")
        print(f"\n=== [{i}] {sid} ({kind}) ===")
        vid = create_video(full, seconds=secs, ref=ref)
        if not poll_video(vid, sid):
            raise SystemExit(f"сцена {sid} не сгенерилась (id={vid}) — перезапусти с index {i}")
        dst = RAW / f"{sid}.mp4"
        kb = download_video(vid, dst) // 1024
        print(f"    -> {dst} ({kb} KB)")
        # seed для следующей сцены (если она chain)
        if i + 1 < len(SCENES) and SCENES[i + 1][1] == "chain":
            nxt = SCENES[i + 1][0]
            last_frame(dst, SEED / f"{nxt}_seed.png")
            print(f"    seed -> {nxt}_seed.png")
    print("\nOK: сцены в public/scroll/raw/")


if __name__ == "__main__":
    main()
