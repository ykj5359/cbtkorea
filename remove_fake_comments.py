# -*- coding: utf-8 -*-
"""
remove_fake_comments.py — 시험 페이지의 가짜 AI 댓글(view-reply) 전량 제거
=======================================================================
각 문항의 <ul class="view-reply"> ... </ul> 내용을 비운다(컨테이너는 유지).
문제·정답·해설(reply collapse)·채점 기능은 그대로 보존.
멱등: 이미 비어 있으면 변화 없음.
대상: CBT/**/*.html (백업/복사본 제외)
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")
OPEN_RE = re.compile(r'<ul class="view-reply">')
TAG_RE = re.compile(r'<ul\b|</ul>')


def empty_view_reply(text: str) -> tuple[str, int]:
    out = []
    i = 0
    removed = 0
    while True:
        m = OPEN_RE.search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        depth = 0
        j = m.end()
        for mm in TAG_RE.finditer(text[m.start():]):
            depth += -1 if mm.group().startswith('</') else 1
            if depth == 0:
                j = m.start() + mm.end()
                break
        inner = text[m.end():j - len('</ul>')]
        if inner.strip():
            removed += 1
        out.append('<ul class="view-reply"></ul>')
        i = j
    return ''.join(out), removed


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
    if 'view-reply' not in text:
        return "clean"
    new, removed = empty_view_reply(text)
    if new == text:
        return "clean"
    try:
        path.write_bytes(new.encode(enc))
    except Exception:
        return "error"
    return "modified"


def main():
    files = [f for f in ROOT.rglob("*.html")
             if "백업" not in str(f) and "복사본" not in str(f)]
    total = len(files)
    print(f"{total:,}개 파일 처리...", flush=True)
    counts = {}
    for i, p in enumerate(files, 1):
        s = fix(p)
        counts[s] = counts.get(s, 0) + 1
        if i % 3000 == 0:
            print(f"  {i:,}/{total:,} | modified={counts.get('modified',0):,}", flush=True)
    print("=" * 44, flush=True)
    for k in ("modified", "clean", "empty", "error"):
        if counts.get(k):
            print(f"  {k:9s}: {counts[k]:,}", flush=True)


if __name__ == "__main__":
    main()
