"""
rename_exam.py — 시험 파일(14k) 일괄:
  1) '시험지 다운로드'(print-btn) 버튼 제거
  2) 'CBT KOREA' → 'CBT 기출문제'
대상: CBT/**/*.html  (백업/복사본 제외)
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")
OLD, NEW = "CBT KOREA", "CBT 기출문제"
PRINT_BTN = re.compile(r'<button[^>]*\bprint-btn\b[^>]*>[\s\S]*?</button>\s*', re.IGNORECASE)


def fix(path: Path) -> tuple[str, int, int]:
    try:
        raw = path.read_bytes()
    except Exception:
        return "error", 0, 0
    if not raw:
        return "empty", 0, 0
    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949"); enc = "cp949"
        except UnicodeDecodeError:
            return "error", 0, 0

    new, nb = PRINT_BTN.subn("", text)
    nk = new.count(OLD)
    if nk:
        new = new.replace(OLD, NEW)
    if new == text:
        return "clean", 0, 0
    try:
        path.write_bytes(new.encode(enc))
    except Exception:
        return "error", 0, 0
    return "modified", nb, nk


def main():
    files = [f for f in ROOT.rglob("*.html")
             if "백업" not in str(f) and "복사본" not in str(f)]
    total = len(files)
    print(f"{total:,}개 파일 처리...", flush=True)
    counts = {"modified": 0, "clean": 0, "empty": 0, "error": 0}
    btn_removed = 0
    kor = 0
    for i, p in enumerate(files, 1):
        s, nb, nk = fix(p)
        counts[s] += 1
        btn_removed += nb
        kor += nk
        if i % 2000 == 0:
            print(f"  {i:,}/{total:,} | modified={counts['modified']:,} 버튼제거={btn_removed:,} 이름치환={kor:,}", flush=True)
    print("=" * 46, flush=True)
    for k, v in counts.items():
        print(f"  {k:9s}: {v:,}", flush=True)
    print(f"  제거된 다운로드 버튼: {btn_removed:,}", flush=True)
    print(f"  CBT KOREA 치환: {kor:,}", flush=True)


if __name__ == "__main__":
    main()
