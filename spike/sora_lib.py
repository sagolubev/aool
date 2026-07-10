#!/usr/bin/env python3
"""Batch-хелперы Sora/GPT-Image на Azure (нативная OpenAI-схема).

Функции создают job'ы (async) и поллят. Импортируется из итерационных скриптов.
"""
import json, mimetypes, re, time, urllib.request, urllib.error, uuid
from pathlib import Path

ENDPOINT = "https://g42-openai-sweden-central.openai.azure.com"
V = "api-version=preview"
OUT = Path(__file__).parent / "out"

STYLE = (
    "Cinematic 35mm lens, golden-hour natural light, warm neutral palette of oak wood, "
    "travertine stone, brass and linen, premium minimalist countryside estate, slow "
    "deliberate steady camera, shallow depth of field, locked architectural geometry, "
    "no morphing, no warping, no distortion, no text or logos, photoreal high-end "
    "real-estate film."
)


def key():
    for l in (Path.home() / ".codex/config.toml").read_text().splitlines():
        if not l.strip().startswith("#"):
            m = re.search(r'"api-key"\s*=\s*"([^"]+)"', l)
            if m:
                return m.group(1)
    raise SystemExit("no key")


K = key()


def _req(url, method="GET", body=None, ctype=None, timeout=120):
    h = {"api-key": K}
    if ctype:
        h["Content-Type"] = ctype
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as x:
            return x.status, x.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _multipart(fields, filefield, filepath):
    b = "----b" + uuid.uuid4().hex
    nl = b"\r\n"
    out = b""
    for k, v in fields.items():
        out += b"--" + b.encode() + nl
        out += f'Content-Disposition: form-data; name="{k}"'.encode() + nl + nl + str(v).encode() + nl
    ct = mimetypes.guess_type(str(filepath))[0] or "application/octet-stream"
    out += b"--" + b.encode() + nl
    out += f'Content-Disposition: form-data; name="{filefield}"; filename="{filepath.name}"'.encode() + nl
    out += f"Content-Type: {ct}".encode() + nl + nl + filepath.read_bytes() + nl
    out += b"--" + b.encode() + b"--" + nl
    return out, f"multipart/form-data; boundary={b}"


def create_video(prompt, seconds="8", size="1280x720", ref: Path = None, model="sora-2"):
    url = f"{ENDPOINT}/openai/v1/videos?{V}"
    if ref:
        body, ct = _multipart({"model": model, "prompt": prompt, "size": size, "seconds": seconds}, "input_reference", ref)
        s, raw = _req(url, "POST", body, ct)
    else:
        s, raw = _req(url, "POST", json.dumps({"model": model, "prompt": prompt, "size": size, "seconds": seconds}).encode(), "application/json")
    if s >= 400:
        raise SystemExit(f"create_video {s}: {raw.decode()[:400]}")
    return json.loads(raw)["id"]


def poll_video(vid, label=""):
    url = f"{ENDPOINT}/openai/v1/videos/{vid}?{V}"
    print(f"poll {label} {vid[-8:]}", end="", flush=True)
    for _ in range(240):
        time.sleep(5)
        s, raw = _req(url)
        j = json.loads(raw)
        st, p = j.get("status"), j.get("progress")
        print(f" {p}%", end="", flush=True)
        if st in ("completed", "succeeded"):
            print(" done"); return True
        if st in ("failed", "cancelled"):
            print(f"\nFAIL {label}: {json.dumps(j.get('error'), ensure_ascii=False)}"); return False
    print(" timeout"); return False


def download_video(vid, dst: Path):
    s, raw = _req(f"{ENDPOINT}/openai/v1/videos/{vid}/content?{V}")
    if s >= 400:
        raise SystemExit(f"download {s}: {raw.decode()[:300]}")
    dst.write_bytes(raw)
    return len(raw)


def gen_image(prompt, dst: Path, size="1536x1024", model="gpt-image-2"):
    url = f"{ENDPOINT}/openai/v1/images/generations?{V}"
    body = json.dumps({"model": model, "prompt": prompt, "size": size, "n": 1}).encode()
    s, raw = _req(url, "POST", body, "application/json", timeout=180)
    if s >= 400:
        raise SystemExit(f"gen_image {s}: {raw.decode()[:400]}")
    d = json.loads(raw)["data"][0]
    import base64
    if d.get("b64_json"):
        dst.write_bytes(base64.b64decode(d["b64_json"]))
    else:
        s2, raw2 = _req(d["url"])
        dst.write_bytes(raw2)
    return dst


def edit_image(prompt, ref: Path, dst: Path, size="1536x1024", model="gpt-image-2"):
    """gpt-image-2 image-edit: перерисовать по референс-картинке (multipart)."""
    body, ct = _multipart({"model": model, "prompt": prompt, "size": size}, "image", ref)
    s, raw = _req(f"{ENDPOINT}/openai/v1/images/edits?{V}", "POST", body, ct, timeout=240)
    if s >= 400:
        raise SystemExit(f"edit_image {s}: {raw.decode()[:400]}")
    d = json.loads(raw)["data"][0]
    import base64
    if d.get("b64_json"):
        dst.write_bytes(base64.b64decode(d["b64_json"]))
    else:
        s2, raw2 = _req(d["url"])
        dst.write_bytes(raw2)
    return dst
