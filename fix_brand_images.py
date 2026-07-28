"""
fix_brand_images.py
===================
CBT KOREA — 시험 HTML 전체 브랜드/이미지 정리

1. 원격 문제 이미지  https://cbtbank.kr/images/xx/examid/file.gif  → images/file.gif (로컬)
2. 프로필 이미지     https://cbtbank.kr/data/member_image/... 등    → ../../img/no_profile.svg
3. comcbt.com   → cbtkorea.kr
4. cbtbank.kr   → cbtkorea.kr
5. CBT문제은행   → CBT KOREA
6. cbt문제은행   → cbtkorea
7. cbtbank(잔여) → cbtkorea (대소문자 무관)

대상: E:/00.CBT/CBT/**/*.html  (백업/복사본 폴더 제외)
실행: python fix_brand_images.py
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")

# 순서 중요: 구체적 패턴 → 일반 패턴
RE_Q_IMG = re.compile(
    r'https?://(?:www\.)?(?:cbtbank|cbtkorea)\.kr/images/[^/"\'\s]+/[^/"\'\s]+/([^/"\'\s?]+)(?:\?[^"\'\s]*)?',
    re.IGNORECASE)
RE_PROFILE = re.compile(
    r'https?://(?:www\.)?(?:cbtbank|cbtkorea)\.kr/(?:data/member_image/[^"\'\s]+|img/no_profile\.gif[^"\'\s]*)',
    re.IGNORECASE)
RE_COMCBT   = re.compile(r'(?:www\.)?comcbt\.com', re.IGNORECASE)
RE_BANK_KR  = re.compile(r'cbtbank\.kr', re.IGNORECASE)
RE_BRAND_KO_UP = re.compile(r'CBT문제은행')
RE_BRAND_KO_LO = re.compile(r'cbt문제은행')
RE_BANK_REST   = re.compile(r'cbtbank', re.IGNORECASE)

PROFILE_LOCAL = '../../img/no_profile.svg'


def fix_text(text: str) -> tuple[str, int]:
    n_total = 0

    def sub_count(pattern, repl, s):
        nonlocal n_total
        new, n = pattern.subn(repl, s)
        n_total += n
        return new

    text = sub_count(RE_Q_IMG,   r'images/\1', text)
    text = sub_count(RE_PROFILE, PROFILE_LOCAL, text)
    text = sub_count(RE_COMCBT,  'cbtkorea.kr', text)
    text = sub_count(RE_BANK_KR, 'cbtkorea.kr', text)
    text = sub_count(RE_BRAND_KO_UP, 'CBT KOREA', text)
    text = sub_count(RE_BRAND_KO_LO, 'cbtkorea', text)
    text = sub_count(RE_BANK_REST,   'cbtkorea', text)
    return text, n_total


def fix_file(path: Path) -> tuple[str, int]:
    try:
        raw = path.read_bytes()
    except Exception:
        return "error", 0
    if not raw:
        return "empty", 0

    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949")
            enc = "cp949"
        except UnicodeDecodeError:
            return "error", 0

    new_text, n = fix_text(text)
    if n == 0:
        return "clean", 0
    try:
        path.write_bytes(new_text.encode(enc))
    except Exception:
        return "error", 0
    return "modified", n


def main() -> None:
    files = [
        f for f in ROOT.rglob("*.html")
        if "백업" not in str(f) and "복사본" not in str(f)
    ]
    total = len(files)
    print(f"시험 파일 {total:,}개 스캔...")

    counts = {"modified": 0, "clean": 0, "empty": 0, "error": 0}
    repl_total = 0
    for i, p in enumerate(files, 1):
        status, n = fix_file(p)
        counts[status] += 1
        repl_total += n
        if i % 2000 == 0:
            print(f"  ... {i:,}/{total:,} | modified={counts['modified']:,} repl={repl_total:,}")

    print("=" * 50)
    for k, v in counts.items():
        print(f"  {k:10s}: {v:,}")
    print(f"  치환 총계  : {repl_total:,}")


if __name__ == "__main__":
    main()
