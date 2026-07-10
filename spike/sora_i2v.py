#!/usr/bin/env python3
"""Sora-2 image-to-video спайк: генерирует клип из референс-картинки (multipart).

POST /openai/v1/videos с полем input_reference=<файл>. Проверяем, что Sora-2
принимает реальное фото/рендер с сайта и делает на его основе похожий пролёт.

Запуск: python3 spike/sora_i2v.py <ref.png> "<prompt>" [seconds] [size]
"""
import json
import mimetypes
import re
import sys
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path

ENDPOINT = "https://g42-openai-sweden-central.openai.azure.com"
API_VERSION = "preview"
DEPLOYMENT = "sora-2"
OUT = Path(__file__).parent / "out"


def load_key():
    for line in (Path.home() / ".codex" / "config.toml").read_text().splitlines():
        if line.strip().startswith("#"):
            continue
        m = re.search(r'"api-key"\s*=\s*"([^"]+)"', line)
        if m:
            return m.group(1)
    raise SystemExit("no key")


def multipart(fields: dict, filefield: str, filepath: Path):
    boundary = "----spike" + uuid.uuid4().hex
    nl = b"\r\n"
    body = b""
    for k, v in fields.items():
        body += b"--" + boundary.encode() + nl
        body += f'Content-Disposition: form-data; name="{k}"'.encode() + nl + nl
        body += str(v).encode() + nl
    ctype = mimetypes.guess_type(str(filepath))[0] or "application/octet-stream"
    body += b"--" + boundary.encode() + nl
    body += f'Content-Disposition: form-data; name="{filefield}"; filename="{filepath.name}"'.encode() + nl
    body += f"Content-Type: {ctype}".encode() + nl + nl
    body += filepath.read_bytes() + nl
    body += b"--" + boundary.encode() + b"--" + nl
    return body, f"multipart/form-data; boundary={boundary}"


def req(url, key, method="GET", body=None, ctype=None):
    headers = {"api-key": key}
    if ctype:
        headers["Content-Type"] = ctype
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main():
    ref = Path(sys.argv[1])
    prompt = sys.argv[2] if len(sys.argv) > 2 else (
        "Slow cinematic camera flight diving toward this scene, gentle parallax, "
        "soft natural light, keep the architecture and layout of the reference"
    )
    seconds = sys.argv[3] if len(sys.argv) > 3 else "4"
    size = sys.argv[4] if len(sys.argv) > 4 else "1280x720"
    key = load_key()
    OUT.mkdir(exist_ok=True)
    base = f"{ENDPOINT}/openai/v1/videos"
    v = f"api-version={API_VERSION}"

    print(f"[1/3] i2v create  ref={ref.name} size={size} seconds={seconds}")
    body, ctype = multipart(
        {"model": DEPLOYMENT, "prompt": prompt, "size": size, "seconds": seconds},
        "input_reference", ref)
    status, raw = req(f"{base}?{v}", key, "POST", body, ctype)
    print(f"      HTTP {status}")
    if status >= 400:
        print(raw.decode()[:2500]); raise SystemExit(1)
    vid = json.loads(raw)["id"]
    print(f"      id={vid}")

    print("[2/3] poll", end="", flush=True)
    done = False
    for _ in range(180):
        time.sleep(5)
        status, raw = req(f"{base}/{vid}?{v}", key)
        j = json.loads(raw)
        st, prog = j.get("status"), j.get("progress")
        print(f" {st}{'('+str(prog)+'%)' if prog is not None else ''}", end="", flush=True)
        if st in ("completed", "succeeded"):
            done = True; break
        if st in ("failed", "cancelled"):
            print(f"\n      error={json.dumps(j.get('error'), ensure_ascii=False)}")
            raise SystemExit(1)
    print()
    if not done:
        raise SystemExit("timeout")

    status, raw = req(f"{base}/{vid}/content?{v}", key)
    if status >= 400:
        print(raw.decode()[:2000]); raise SystemExit(1)
    dst = OUT / f"i2v_{ref.stem}_{vid[-8:]}.mp4"
    dst.write_bytes(raw)
    print(f"[3/3] OK -> {dst} ({len(raw)//1024} KB)")


if __name__ == "__main__":
    main()
