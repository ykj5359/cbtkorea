"""
bump_script_version.py
======================
시험 파일의 cbt-auth.js / cbt-exam.js 스크립트 태그에 버전 쿼리(?v=2)를 붙여
브라우저가 캐시된 구버전 스크립트를 쓰지 않도록 한다.

멱등: 이미 ?v=2 면 건너뜀. (이전 버전 ?v=N 은 v=2 로 갱신)
실행: python bump_script_version.py
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")
VER  = "5"

RE_AUTH = re.compile(r'src="(\.\./\.\./cbt-auth\.js)(?:\?v=\d+)?"')
RE_EXAM = re.compile(r'src="(\.\./\.\./cbt-exam\.js)(?:\?v=\d+)?"')


def fix_file(path: Path) -> str:
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
            text = raw.decode("cp949")
            enc = "cp949"
        except UnicodeDecodeError:
            return "error"

    new = RE_AUTH.sub(r'src="\1?v=' + VER + '"', text)
    new = RE_EXAM.sub(r'src="\1?v=' + VER + '"', new)
    if new == text:
        return "skip"
    try:
        path.write_bytes(new.encode(enc))
    except Exception:
        return "error"
    return "modified"


def main() -> None:
    files = [
        f for f in ROOT.rglob("*.html")
        if "백업" not in str(f) and "복사본" not in str(f)
    ]
    total = len(files)
    print(f"{total:,}개 파일 처리...", flush=True)
    counts: dict[str, int] = {}
    for i, p in enumerate(files, 1):
        s = fix_file(p)
        counts[s] = counts.get(s, 0) + 1
        if i % 2000 == 0:
            print(f"  {i:,}/{total:,} {counts}", flush=True)
    print("완료:", counts, flush=True)


if __name__ == "__main__":
    main()
