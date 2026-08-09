# -*- coding: utf-8 -*-
"""
inject_canonical_all.py — 기출문제(CBT/**) + 종목목록(CBT-list/**) 전체에
self-referencing canonical 태그 삽입.
canonical = https://cbtkorea.kr/ + (퍼센트 인코딩된 상대경로)
멱등: <!-- CANONICAL-CBT --> 마커 있으면 건너뜀. </head> 앞 삽입.
"""
from __future__ import annotations
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(r"E:\00.CBT")
BASE = "https://cbtkorea.kr/"
MARKER = "<!-- CANONICAL-CBT -->"
HEAD_RE = re.compile(r'</head\s*>', re.IGNORECASE)


def targets():
    for f in (ROOT / "CBT").rglob("*.html"):
        if "백업" not in str(f) and "복사본" not in str(f):
            yield f
    for f in (ROOT / "CBT-list").glob("*.html"):
        if "복사본" not in str(f):
            yield f


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
    rel = path.relative_to(ROOT).as_posix()
    url = BASE + quote(rel, safe="/")
    block = f'\n{MARKER}\n<link rel="canonical" href="{url}">\n'
    new = text[:m.start()] + block + text[m.start():]
    try:
        path.write_bytes(new.encode(enc))
    except Exception:
        return "error"
    return "modified"


def main():
    files = list(targets())
    total = len(files)
    print(f"{total:,}개 파일 canonical 삽입...", flush=True)
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
