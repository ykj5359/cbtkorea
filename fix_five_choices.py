# -*- coding: utf-8 -*-
"""
fix_five_choices.py — 5지선다 보기 번호 표시 수정
================================================
문제: 시험 페이지 CSS가 보기 번호를 ①~④(nth-child 4)까지만 정의 →
      5번째 보기가 기본 counter(decimal-leading-zero) = "05" 로 표시됨.
수정: nth-child(4) 규칙 뒤에 ⑤⑥⑦⑧ (5~8) 규칙 삽입.
동시에 cbt-auth.js / cbt-exam.js 참조 버전을 v=8 로 올려
(채점 모달 ⑤ 지원 수정분) 캐시를 무효화한다.
멱등: nth-child(5)::before 가 이미 있으면 CSS 삽입 생략.
대상: CBT/**/*.html (백업/복사본 제외)
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")
VER = "8"

# nth-child(4) 규칙 (들여쓰기 캡처)
RULE4_RE = re.compile(
    r'([ \t]*)(\.question-choice ol\.circlednumbers li:nth-child\(4\)::before\s*\{\s*content:\s*"④";\s*\})')

VER_RE = re.compile(r'(src="\.\./\.\./cbt-(?:auth|exam)\.js)(?:\?v=\d+)?(")')


def build_rules(indent: str) -> str:
    lines = []
    for n, ch in ((5, "⑤"), (6, "⑥"), (7, "⑦"), (8, "⑧")):
        lines.append(
            f'{indent}.question-choice ol.circlednumbers li:nth-child({n})::before {{ content: "{ch}"; }}')
    return "\n" + "\n".join(lines)


def fix(path: Path) -> tuple[str, bool, bool]:
    try:
        raw = path.read_bytes()
    except Exception:
        return "error", False, False
    if not raw:
        return "empty", False, False
    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949"); enc = "cp949"
        except UnicodeDecodeError:
            return "error", False, False

    css_added = False
    if "li:nth-child(5)::before" not in text:
        def repl(m):
            return m.group(1) + m.group(2) + build_rules(m.group(1))
        new, n = RULE4_RE.subn(repl, text, count=1)
        if n:
            text = new
            css_added = True

    text2, nv = VER_RE.subn(r"\1?v=" + VER + r"\2", text)
    ver_bumped = text2 != text
    text = text2

    if not css_added and not ver_bumped:
        return "clean", False, False
    try:
        path.write_bytes(text.encode(enc))
    except Exception:
        return "error", False, False
    return "modified", css_added, ver_bumped


def main():
    files = [f for f in ROOT.rglob("*.html")
             if "백업" not in str(f) and "복사본" not in str(f)]
    total = len(files)
    print(f"{total:,}개 파일 처리...", flush=True)
    counts = {}
    css_n = ver_n = 0
    for i, p in enumerate(files, 1):
        s, c, v = fix(p)
        counts[s] = counts.get(s, 0) + 1
        css_n += c
        ver_n += v
        if i % 3000 == 0:
            print(f"  {i:,}/{total:,} | css={css_n:,} ver={ver_n:,}", flush=True)
    print("=" * 44, flush=True)
    for k in ("modified", "clean", "empty", "error"):
        if counts.get(k):
            print(f"  {k:9s}: {counts[k]:,}", flush=True)
    print(f"  CSS(⑤~⑧) 삽입: {css_n:,} / 버전 v={VER} 갱신: {ver_n:,}", flush=True)


if __name__ == "__main__":
    main()
