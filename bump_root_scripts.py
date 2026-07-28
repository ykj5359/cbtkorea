"""
bump_root_scripts.py
====================
루트 페이지들이 참조하는 cbt-auth.js / cbt-exam.js / cbt-qnet-data.js 에
버전 쿼리(?v=3)를 붙여 브라우저 캐시된 구버전 사용을 방지한다.
멱등: 이미 ?v=3 이면 그대로.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT")
VER = "6"
FILES = ["index.html", "notice.html", "videos.html", "exams.html",
         "community.html", "mypage.html", "login.html", "signup.html",
         "cbt-qnet.html", "cbt-exam-sim.html"]
SCRIPTS = ["cbt-auth.js", "cbt-exam.js", "cbt-qnet-data.js"]


def bump(text: str) -> tuple[str, int]:
    n = 0
    for s in SCRIPTS:
        # src="cbt-auth.js"  또는  src="cbt-auth.js?v=2"  → ?v=3
        pat = re.compile(r'(src=["\'])(' + re.escape(s) + r')(?:\?v=\d+)?(["\'])')
        text, c = pat.subn(r'\1\2?v=' + VER + r'\3', text)
        n += c
    return text, n


def main() -> None:
    for name in FILES:
        p = ROOT / name
        if not p.exists():
            print(f"  없음: {name}"); continue
        raw = p.read_bytes()
        try:
            text = raw.decode("utf-8"); enc = "utf-8"
        except UnicodeDecodeError:
            text = raw.decode("cp949"); enc = "cp949"
        new, n = bump(text)
        if new != text:
            p.write_bytes(new.encode(enc))
            print(f"  OK: {name} ({n}개 참조)")
        else:
            print(f"  변경없음: {name}")


if __name__ == "__main__":
    main()
