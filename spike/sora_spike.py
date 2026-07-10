#!/usr/bin/env python3
"""Sora-2 spike: генерирует один клип через Azure OpenAI, нативная Sora-схема.

Роут (OpenAI-native, подтверждён на g42-sweden-central):
  1. POST /openai/v1/videos            -> {id, status: queued}
  2. GET  /openai/v1/videos/{id}       -> poll до completed/failed
  3. GET  /openai/v1/videos/{id}/content -> mp4

Креды: api-key активного azure-провайдера из ~/.codex/config.toml.
Запуск: python3 spike/sora_spike.py ["<prompt>"] [seconds] [size]
"""
import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ENDPOINT = "https://g42-openai-sweden-central.openai.azure.com"
API_VERSION = "preview"
DEPLOYMENT = "sora-2"
OUT = Path(__file__).parent / "out"


def load_key() -> str:
    for line in (Path.home() / ".codex" / "config.toml").read_text().splitlines():
        if line.strip().startswith("#"):
            continue
        m = re.search(r'"api-key"\s*=\s*"([^"]+)"', line)
        if m:
            return m.group(1)
    raise SystemExit("api-key не найден в ~/.codex/config.toml")


def req(url, key, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"api-key": key}
    if body is not None:
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else (
        "Isometric miniature diorama of a serene forest village in soft morning "
        "light, tilt-shift toy world, camera slowly diving from above into the "
        "trees toward a modern wooden cabin, cinematic, warm palette, stylized 3D render"
    )
    seconds = sys.argv[2] if len(sys.argv) > 2 else "4"
    size = sys.argv[3] if len(sys.argv) > 3 else "1280x720"
    key = load_key()
    OUT.mkdir(exist_ok=True)
    base = f"{ENDPOINT}/openai/v1/videos"
    v = f"api-version={API_VERSION}"

    print(f"[1/3] create  model={DEPLOYMENT} size={size} seconds={seconds}")
    status, raw = req(f"{base}?{v}", key, "POST",
                      {"model": DEPLOYMENT, "prompt": prompt, "size": size, "seconds": seconds})
    print(f"      HTTP {status}")
    if status >= 400:
        print(raw.decode()[:2000]); raise SystemExit(1)
    job = json.loads(raw)
    vid = job.get("id")
    print(f"      id={vid} status={job.get('status')}")

    print("[2/3] poll", end="", flush=True)
    done = False
    for _ in range(180):  # до ~15 мин
        time.sleep(5)
        status, raw = req(f"{base}/{vid}?{v}", key)
        j = json.loads(raw)
        st = j.get("status")
        prog = j.get("progress")
        print(f" {st}{'('+str(prog)+'%)' if prog is not None else ''}", end="", flush=True)
        if st in ("completed", "succeeded"):
            done = True; break
        if st in ("failed", "cancelled"):
            print(f"\n      error={j.get('error')}")
            print(json.dumps(j, ensure_ascii=False)[:2000]); raise SystemExit(1)
    print()
    if not done:
        raise SystemExit("таймаут поллинга")

    print(f"[3/3] download {vid}/content")
    status, raw = req(f"{base}/{vid}/content?{v}", key)
    if status >= 400:
        print(raw.decode()[:2000]); raise SystemExit(1)
    dst = OUT / f"{vid}.mp4"
    dst.write_bytes(raw)
    print(f"      OK -> {dst}  ({len(raw)//1024} KB)")
    print(f"\nПросмотр: open {dst}")


if __name__ == "__main__":
    main()
