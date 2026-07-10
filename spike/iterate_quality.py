#!/usr/bin/env python3
"""Итерация качества: запускает несколько job'ов сразу, поллит, скачивает.

  A) 12s непрерывный дубль экстерьер->интерьер (i2v из рендера Вода) + style lock
  B) управляемый интерьер: gpt-image-2 стилл -> i2v 8s
  C) следующая сцена: лес/въезд t2v 8s в том же стиле
"""
from pathlib import Path
from sora_lib import STYLE, create_video, poll_video, download_video, gen_image, OUT

REF = Path(__file__).parent / "ref"

jobs = {}

# A) непрерывный дубль
jobs["A_journey12"] = create_video(
    f"{STYLE} Begin on this modern two-storey house by the water at golden hour. "
    "The camera glides slowly down and forward, passing through the floor-to-ceiling "
    "glass facade and seamlessly entering a bright double-height open-plan living "
    "space: a designer boucle sofa, a sculptural coffee table, a stone-clad fireplace, "
    "wide oak floors, an open kitchen with a large marble island, a minimalist dining "
    "area with statement pendant lights, soft linen curtains. Preserve the exact "
    "architecture, glazing and materials of the reference. One continuous take.",
    seconds="12", ref=REF / "voda_1280.png")

# C) следующая сцена (t2v, лес/въезд в посёлок)
jobs["C_forest8"] = create_video(
    f"{STYLE} Aerial camera drifting slowly over a serene birch and pine forest at "
    "25 km from the city, morning mist between the trees, a winding road leading toward "
    "a premium gated countryside village in the distance, calm and inviting. One "
    "continuous establishing shot.",
    seconds="8")

print("created:", {k: v[-8:] for k, v in jobs.items()})

# B) управляемый интерьер: сначала стилл
print("gen interior still (gpt-image-2)...")
still = gen_image(
    f"Interior design photograph. {STYLE} A double-height open-plan living room of a "
    "luxury countryside house: low boucle sofa, stone fireplace, oak floors, marble "
    "kitchen island, dining with pendant lights, floor-to-ceiling windows overlooking "
    "water and forest, golden-hour light. Editorial, symmetrical, expensive, serene.",
    OUT / "interior_still.png", size="1536x1024")
print("still ->", still)
jobs["B_interior8"] = create_video(
    f"{STYLE} Slow cinematic camera gliding forward through this luxury living room, "
    "gentle parallax past the sofa and fireplace toward the marble kitchen island and "
    "the windows, revealing the layout. Preserve the exact furniture, materials and "
    "layout of the reference. One continuous take.",
    seconds="8", ref=OUT / "interior_still.png")

print("created interior i2v:", jobs["B_interior8"][-8:])

# poll + download all
results = {}
for name, vid in jobs.items():
    ok = poll_video(vid, name)
    if ok:
        dst = OUT / f"{name}.mp4"
        kb = download_video(vid, dst) // 1024
        results[name] = f"{dst}  {kb} KB"
    else:
        results[name] = "FAILED"

print("\n=== RESULTS ===")
for k, v in results.items():
    print(f"{k}: {v}")
