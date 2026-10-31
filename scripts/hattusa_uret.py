#!/usr/bin/env python3
"""Hattuşa videosunu LTX API (V2) ile üretir ve sahneleri tek videoda birleştirir.

Prompt'lar hattusa_video_plani.md dosyasındaki "## Sahne N" bölümlerinden okunur.

Kullanım:
    export LTX_API_KEY=...            # LTX API anahtarı
    python scripts/hattusa_uret.py     # çıktı: cikti/hattusa/hattusa.mp4

Seçenekler için: python scripts/hattusa_uret.py --help
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "hattusa_video_plani.md"

# Sahneler arası geçişler (plandaki tabloya göre)
TRANSITIONS = ["fade", "fadeblack", "smoothleft"]
XFADE = 0.8
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def read_prompts(plan: Path) -> list[str]:
    text = plan.read_text(encoding="utf-8")
    prompts = re.findall(r"^## Sahne \d+[^\n]*\n+```\n(.*?)\n```", text, flags=re.M | re.S)
    if len(prompts) != 4:
        sys.exit(f"Planda 4 sahne prompt'u bekleniyordu, {len(prompts)} bulundu.")
    return [p.strip() for p in prompts]


class LTX:
    def __init__(self, base: str, key: str | None):
        self.base = base.rstrip("/")
        self.s = requests.Session()
        if key:
            self.s.headers["Authorization"] = f"Bearer {key}"

    def _req(self, method: str, url: str, **kw) -> requests.Response:
        for attempt in range(5):
            try:
                r = self.s.request(method, url, timeout=120, **kw)
            except requests.RequestException as e:
                err = str(e)
            else:
                if r.status_code < 500 and r.status_code != 429:
                    return r
                err = f"HTTP {r.status_code}: {r.text[:200]}"
            wait = 2 ** (attempt + 1)
            print(f"  geçici hata ({err}), {wait} sn sonra tekrar...", flush=True)
            time.sleep(wait)
        raise RuntimeError(f"{method} {url} başarısız: {err}")

    def generate(self, name: str, payload: dict, out: Path) -> Path:
        r = self._req("POST", f"{self.base}/v2/text-to-video", json=payload)
        if r.status_code != 202:
            raise RuntimeError(f"{name}: gönderim reddedildi — HTTP {r.status_code}: {r.text}")
        job_id = r.json()["id"]
        print(f"[{name}] iş gönderildi: {job_id}", flush=True)
        last = None
        while True:
            time.sleep(random.uniform(5, 7))
            r = self._req("GET", f"{self.base}/v2/text-to-video/{job_id}")
            r.raise_for_status()
            st = r.json()
            if st["status"] != last:
                print(f"[{name}] durum: {st['status']}", flush=True)
                last = st["status"]
            if st["status"] == "failed":
                raise RuntimeError(f"{name}: iş başarısız — {st.get('error')}")
            if st["status"] == "completed":
                break
        video = self._req("GET", st["result"]["video_url"])
        video.raise_for_status()
        out.write_bytes(video.content)
        print(f"[{name}] indirildi: {out} ({len(video.content) / 1e6:.1f} MB)", flush=True)
        return out


def duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]
    )
    return float(out.strip())


def merge(clips: list[Path], out: Path) -> None:
    durs = [duration(c) for c in clips]
    print("Klip süreleri:", ", ".join(f"{d:.2f}" for d in durs))
    parts, acc, prev = [], durs[0], "0:v"
    for i, (trans, d) in enumerate(zip(TRANSITIONS, durs[1:]), start=1):
        offset = acc - XFADE
        label = f"v{i}"
        parts.append(f"[{prev}][{i}:v]xfade=transition={trans}:duration={XFADE}:offset={offset:.3f}[{label}]")
        prev, acc = label, offset + d
    fade = "alpha='if(lt(t,1.6),t-0.8,if(gt(t,2.8),3.6-t,1))'"
    title = (
        f"[{prev}]drawtext=fontfile={FONT}:text='HATTUŞA':fontsize=96:fontcolor=white:"
        f"x=(w-tw)/2:y=(h-th)/2-40:enable='between(t,0.8,3.6)':{fade},"
        f"drawtext=fontfile={FONT}:text='M.Ö. 1650 – 1180':fontsize=44:fontcolor=white:"
        f"x=(w-tw)/2:y=(h-th)/2+60:enable='between(t,0.8,3.6)':{fade}[v]"
    )
    parts.append(title)
    parts.append(f"[0:a][1:a]acrossfade=d={XFADE}[a1]")
    parts.append(f"[a1][2:a]acrossfade=d={XFADE}[a2]")
    parts.append(f"[a2][3:a]acrossfade=d={XFADE}[a]")
    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-i", str(c)]
    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", str(out),
    ]
    subprocess.run(cmd, check=True)
    print(f"Bitti: {out} ({duration(out):.1f} sn)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="ltx-2-5-pro", help="ltx-2-5-pro (en yüksek kalite) veya ltx-2-5-fast")
    ap.add_argument("--resolution", default="1920x1080")
    ap.add_argument("--duration", type=int, default=6, help="Sahne süresi (sn). LTX-2.5 Pro: 6, 8 veya 10")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "cikti" / "hattusa")
    ap.add_argument("--api-base", default=os.environ.get("LTX_API_BASE", "https://api.ltx.video"))
    ap.add_argument("--only-merge", action="store_true", help="Var olan s1..s4.mp4 dosyalarını sadece birleştir")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    clips = [args.out_dir / f"s{i}.mp4" for i in range(1, 5)]

    if not args.only_merge:
        client = LTX(args.api_base, os.environ.get("LTX_API_KEY"))
        prompts = read_prompts(PLAN)
        todo = [(i, p) for i, p in enumerate(prompts) if not clips[i].exists()]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            futs = [
                ex.submit(
                    client.generate,
                    f"Sahne {i + 1}",
                    {
                        "prompt": p,
                        "model": args.model,
                        "duration": args.duration,
                        "resolution": args.resolution,
                        "fps": args.fps,
                        "generate_audio": True,
                    },
                    clips[i],
                )
                for i, p in todo
            ]
            errors = [f.exception() for f in futs if f.exception()]
        if errors:
            for e in errors:
                print("HATA:", e, file=sys.stderr)
            sys.exit("Bazı sahneler üretilemedi; tekrar çalıştırınca yalnızca eksikler üretilir.")

    merge(clips, args.out_dir / "hattusa.mp4")


if __name__ == "__main__":
    main()
