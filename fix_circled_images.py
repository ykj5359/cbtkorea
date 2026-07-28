"""
fix_circled_images.py
=====================
시험 HTML의 이미지 경로에 섞인 원문자(①②③④⑤ …, U+2460~U+24FF)로
깨진 파일명을 각 파일의 실제 stem 으로 복원한다.

예) 가구제작기능사/mn20050130.html
    깨짐:  src="images/mn20⑤0130m13.gif"   (실제파일 없음)
    복원:  src="images/mn20050130m13.gif"  (실제파일 존재)

원리:
  한 시험 HTML(파일 stem = S)의 문제 이미지는 항상 "images/{S}{suffix}" 형식.
  suffix(= m13.gif, m32b1.gif …)는 손상되지 않으므로,
  src 의 id 부분(원문자 포함)을 S 로 교체하면 정확히 복원된다.
  → 원문자가 들어간 src 만 수정하므로 정상 파일은 건드리지 않음(멱등).

실행: python fix_circled_images.py
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")

# src="images/<id><suffix>" 형태. suffix = m<숫자>(b<숫자>|m<숫자>)*.gif
# id 부분(.+?)은 원문자를 포함할 수 있음. \d 는 원문자를 매칭하지 않으므로
#  suffix 는 손상되지 않은 실제 문제 마커에 정확히 정렬된다.
IMG_RE = re.compile(
    r'(src=["\'])images/(.+?)(m\d+(?:[bm]\d+)*\.gif)(["\'])',
    re.IGNORECASE)

# 원문자(circled/parenthesized numbers) 범위
CIRCLED = re.compile(r'[①-⓿㉑-㊿０-９]')


def fix_text(text: str, stem: str) -> tuple[str, int]:
    n = [0]

    def repl(m):
        idpart = m.group(2)
        if CIRCLED.search(idpart):
            n[0] += 1
            return m.group(1) + 'images/' + stem + m.group(3) + m.group(4)
        return m.group(0)

    return IMG_RE.sub(repl, text), n[0]


def fix_file(path: Path) -> tuple[str, int]:
    try:
        raw = path.read_bytes()
    except Exception:
        return "error", 0
    if not raw:
        return "empty", 0
    # 원문자가 아예 없으면 빠르게 건너뜀
    if b'\xe2\x91' not in raw and b'\xe2\x92' not in raw and b'\xe2\x93' not in raw:
        # UTF-8 원문자(①=E2 91 A0 …)가 없음. cp949 가능성도 있으니 디코드 후 재확인은 생략(성능).
        # 안전을 위해 디코드 후 처리하되, 대부분 여기서 스킵됨.
        pass

    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949"); enc = "cp949"
        except UnicodeDecodeError:
            return "error", 0

    stem = path.stem
    new, n = fix_text(text, stem)
    if n == 0:
        return "clean", 0
    try:
        path.write_bytes(new.encode(enc))
    except Exception:
        return "error", 0
    return "modified", n


def main() -> None:
    files = [f for f in ROOT.rglob("*.html")
             if "백업" not in str(f) and "복사본" not in str(f)]
    total = len(files)
    print(f"{total:,}개 파일 스캔...", flush=True)
    counts = {"modified": 0, "clean": 0, "empty": 0, "error": 0}
    fixed_refs = 0
    for i, p in enumerate(files, 1):
        s, n = fix_file(p)
        counts[s] += 1
        fixed_refs += n
        if i % 2000 == 0:
            print(f"  {i:,}/{total:,} | modified={counts['modified']:,} refs={fixed_refs:,}", flush=True)
    print("=" * 46, flush=True)
    for k, v in counts.items():
        print(f"  {k:9s}: {v:,}", flush=True)
    print(f"  복원된 이미지 참조: {fixed_refs:,}", flush=True)


if __name__ == "__main__":
    main()
