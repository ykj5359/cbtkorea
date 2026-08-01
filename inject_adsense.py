# -*- coding: utf-8 -*-
"""
inject_adsense.py — 전체 HTML 페이지 <head> 에 Google AdSense 코드 + 메타태그 삽입
======================================================================
게시자 ID: ca-pub-3399466730471372
대상: E:/00.CBT 하위 모든 *.html (백업/복사본 제외)
멱등: 마커(<!-- ADSENSE-CBT -->)가 있으면 건너뜀
삽입 위치: </head> 바로 앞
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT")
MARKER = "<!-- ADSENSE-CBT -->"
PUB = "ca-pub-3399466730471372"

BLOCK = (
    "\n" + MARKER + "\n"
    f'<meta name="google-adsense-account" content="{PUB}">\n'
    f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={PUB}"\n'
    '     crossorigin="anonymous"></script>\n'
)

HEAD_RE = re.compile(r'</head\s*>', re.IGNORECASE)


def fix(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except Exception:
        return "error"
    if not raw:
        return "empty"
    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949"); enc = "cp949"
        except UnicodeDecodeError:
            return "error"

    if MARKER in text:
        return "already"
    m = HEAD_RE.search(text)
    if not m:
        return "no_head"
    new = text[:m.start()] + BLOCK + text[m.start():]
    try:
        path.write_bytes(new.encode(enc))
    except Exception:
        return "error"
    return "modified"


def main():
    files = [f for f in ROOT.rglob("*.html")
             if "백업" not in str(f) and "복사본" not in str(f)]
    total = len(files)
    print(f"{total:,}개 HTML 처리...", flush=True)
    counts = {}
    for i, p in enumerate(files, 1):
        s = fix(p)
        counts[s] = counts.get(s, 0) + 1
        if i % 3000 == 0:
            print(f"  {i:,}/{total:,} | modified={counts.get('modified',0):,}", flush=True)
    print("=" * 44, flush=True)
    for k in ("modified", "already", "no_head", "empty", "error"):
        if counts.get(k):
            print(f"  {k:9s}: {counts[k]:,}", flush=True)


if __name__ == "__main__":
    main()
