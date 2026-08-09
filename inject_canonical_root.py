# -*- coding: utf-8 -*-
"""
inject_canonical_root.py — 주요(루트) 페이지에 canonical 태그 삽입
· index.html → https://cbtkorea.kr/ (홈페이지 표준 URL 통일)
· 그 외 → 자기 자신 URL (self-referencing canonical)
멱등: <!-- CANONICAL-CBT --> 마커 있으면 건너뜀. </head> 앞에 삽입.
"""
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT")
BASE = "https://cbtkorea.kr/"
MARKER = "<!-- CANONICAL-CBT -->"
HEAD_RE = re.compile(r'</head\s*>', re.IGNORECASE)

# 파일명 → canonical URL (index.html 은 루트로)
PAGES = ["index.html", "exams.html", "notice.html", "community.html", "about.html",
         "contact.html", "privacy.html", "terms.html", "videos.html", "mypage.html",
         "cbt-qnet.html", "login.html", "signup.html", "cbt-exam-sim.html"]


def canon_url(name):
    return BASE if name == "index.html" else BASE + name


def fix(name):
    p = ROOT / name
    if not p.exists():
        return f"  없음: {name}"
    raw = p.read_bytes()
    try:
        text = raw.decode("utf-8"); enc = "utf-8"
    except UnicodeDecodeError:
        text = raw.decode("cp949"); enc = "cp949"
    if MARKER in text:
        return f"  이미있음: {name}"
    m = HEAD_RE.search(text)
    if not m:
        return f"  head없음: {name}"
    block = f'\n{MARKER}\n<link rel="canonical" href="{canon_url(name)}">\n'
    new = text[:m.start()] + block + text[m.start():]
    p.write_bytes(new.encode(enc))
    return f"  ✓ {name} → {canon_url(name)}"


for n in PAGES:
    print(fix(n))
