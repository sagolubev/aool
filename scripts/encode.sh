#!/usr/bin/env bash
# scroll-world Step 6 энкод: seekable blob-scrub качество.
# native-res, малый GOP (-g 8), unsharp, faststart, без звука. + webp-постеры.
set -euo pipefail
cd "$(dirname "$0")/.."
raw=public/scroll/raw
out=public/scroll
mkdir -p "$out"
[ -d "$raw" ] || { echo "нет $raw — сначала scripts/gen_scenes.py"; exit 1; }

count=0
for f in "$raw"/*.mp4; do
  [ -e "$f" ] || continue
  id=$(basename "$f" .mp4)
  ffmpeg -y -loglevel error -i "$f" -an -vf "unsharp=5:5:0.8:5:5:0.0" \
    -c:v libx264 -preset medium -crf 24 -pix_fmt yuv420p \
    -g 8 -keyint_min 8 -sc_threshold 0 -movflags +faststart "$out/$id.mp4"
  ffmpeg -y -loglevel error -i "$out/$id.mp4" -frames:v 1 "$out/$id.webp"
  count=$((count+1))
done
echo "encoded $count clips -> $out"