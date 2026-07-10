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

# точное описание архитектуры АУЛ (по реальным рендерам с сайта)
HOUSE_STYLE = (
    "The houses are modern minimalist flat-roof cubic villas: white brick and warm "
    "vertical timber-slat facades, large floor-to-ceiling windows with black frames, "
    "cantilevered volumes, integrated carports with premium cars, ornamental grass "
    "gardens, pine and spruce trees, low stone-and-metal fences with house numbers, "
    "gravel and paved paths. Every house shares this exact architectural language."
)

AERIAL = SEED / "aerial_1280.png"      # аэро-стилл АУЛ (из реального плана посёлка)
UMAP = SEED / "umap.jpg"               # реальный мастер-план (top-down) с сайта
AERIAL_EDIT_PROMPT = (
    "Redraw this settlement master plan as a photoreal angled aerial bird's-eye view "
    "from a low drone at golden hour. Keep the exact same layout, streets, central alley, "
    "pond and plots. The houses are modern minimalist FLAT-ROOF cubic villas: white brick "
    "and warm vertical timber-slat facades, black-framed glazing, carports, ornamental "
    "grass gardens, pine and spruce trees. No pitched or gabled roofs. Warm cinematic light."
)


def ensure_aerial():
    """Аэро-стилл посёлка из реального плана (umap) через gpt-image-2 edit."""
    if AERIAL.exists():
        return
    from sora_lib import edit_image
    crop = SEED / "umap_crop.png"
    if not crop.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(UMAP),
                        "-vf", "crop=1507:848:0:250,scale=1280:720", str(crop)], check=True)
    raw = AERIAL.with_name("aerial_plan.png")
    edit_image(AERIAL_EDIT_PROMPT, crop, raw, size="1536x1024")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-vf",
                    "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
                    str(AERIAL)], check=True)


def last_frame(mp4: Path, dst: Path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(mp4)],
        capture_output=True, text=True).stdout.strip()
    n = int(out)
    # один проход: выбрать последний кадр + привести к 1280x720
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
                    f"select=eq(n\\,{n-1}),"
                    "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
                    "-frames:v", "1", str(dst)], check=True)


# (id, kind, prompt, seconds)
SCENES = [
    ("forest", "t2v",
     "Aerial drift over a serene birch-and-pine forest 25 km from the city, morning mist "
     "between the trees, a single winding empty road. Pure untouched nature, NO houses, no "
     "buildings, no rooftops anywhere. Calm and inviting. End settling into a slow steady "
     "forward glide along the road.", "8"),
    ("gate", "aerial",
     "Slow cinematic drone descent gliding forward over this modern flat-roof countryside "
     "village at golden hour, toward the central landscaped alley with the pond and "
     "amphitheatre. Every roof stays flat. Keep gliding forward, never pulling back.", "8"),
    ("alley", "chain",
     "Continue gliding forward, lower now, along the central landscaped alley between "
     "modern flat-roof villas, past the pond and the small amphitheatre, wide paved paths "
     "and ornamental grasses. End settling forward toward one modern house.", "8"),
    ("house", "anchor",
     "Slow cinematic camera gliding down and forward toward this modern two-storey house "
     "by the water at golden hour, warm interior lights switching on, subtle parallax. "
     "Preserve the exact architecture, glazing and materials of the reference. End "
     "settling as it drifts toward the large glass entrance door.", "8"),
    ("interior", "chain",
     "Continue forward: the large floor-to-ceiling glass entrance door slides open and "
     "the camera glides slowly through the doorway into a bright double-height living "
     "room, taking its time to explore: a designer boucle sofa, a stone-clad fireplace, "
     "wide oak floors, an open kitchen with a large marble island, a minimalist dining "
     "area with statement pendant lights, soft linen curtains, slow gentle parallax "
     "revealing the space. Keep gliding slowly forward toward the far terrace doors.", "12"),
    ("garden", "chain",
     "Continue forward: the camera glides out through the open terrace doors, stepping "
     "OUTSIDE onto a spacious modern outdoor terrace that is FULLY FURNISHED and lived-in. "
     "In the foreground a comfortable outdoor lounge set: a large sofa with cushions, two "
     "lounge armchairs and sunbeds around a low coffee table, a long wooden dining table "
     "with chairs to the side, a built-in barbecue grill. Near the house glass wall stands "
     "a round wooden cold-plunge tub (kupel) with water and gentle steam. Potted plants, "
     "outdoor lamps, ornamental grasses, fruit trees, a calm water view, warm sunset light. "
     "No separate sauna cabin. End settling on the furnished lounge terrace with the tub.", "12"),
]


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else len(SCENES) - 1  # inclusive
    RAW.mkdir(parents=True, exist_ok=True)
    for i, (sid, kind, prompt, secs) in enumerate(SCENES):
        if i < start or i > end:
            continue
        full = f"{STYLE} {prompt}"
        ref = None
        if kind == "anchor":
            ref = VODA
        elif kind == "aerial":
            ensure_aerial()
            ref = AERIAL
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
