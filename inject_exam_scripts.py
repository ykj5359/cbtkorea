"""
inject_exam_scripts.py
======================
CBT KOREA — 시험 HTML 파일 전체에 cbt-auth.js + cbt-exam.js 삽입

삽입 위치: </body> 바로 앞
삽입 내용:
    <!-- CBT-AUTH-V1 -->
    <script src="../../cbt-auth.js"></script>
    <script src="../../cbt-exam.js"></script>

멱등성: 이미 마커(<!-- CBT-AUTH-V1 -->)가 있으면 건너뜀.
경로:   E:/00.CBT/CBT/** 하위 모든 .html 파일 (2단계 깊이)
        ../../cbt-auth.js  →  E:/00.CBT/cbt-auth.js
        ../../cbt-exam.js  →  E:/00.CBT/cbt-exam.js

실행 방법:
    python inject_exam_scripts.py
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT   = Path(r"E:\00.CBT\CBT")
MARKER = "<!-- CBT-AUTH-V1 -->"

INJECT = (
    "\n" + MARKER + "\n"
    '<script src="../../cbt-auth.js"></script>\n'
    '<script src="../../cbt-exam.js"></script>\n'
)

# </body> 매칭 패턴 (대소문자 허용)
BODY_RE = re.compile(r'</body\s*>', re.IGNORECASE)


def fix_file(path: Path) -> tuple[str, str]:
    # ── 읽기 ──
    try:
        raw = path.read_bytes()
    except Exception as e:
        return "error", f"read: {e}"

    if not raw:
        return "empty", ""

    # ── 디코딩 ──
    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949")
            enc  = "cp949"
        except UnicodeDecodeError:
            return "error", "decode failed"

    # ── 멱등성 체크 ──
    if MARKER in text:
        return "already_done", ""

    # ── 패턴 찾기 ──
    m = BODY_RE.search(text)
    if not m:
        return "no_body_tag", ""

    # ── 삽입 ──
    new_text = text[:m.start()] + INJECT + text[m.start():]

    # ── 쓰기 ──
    try:
        path.write_bytes(new_text.encode(enc))
    except Exception as e:
        return "error", f"write: {e}"

    return "modified", ""


def main() -> None:
    if not ROOT.exists():
        print(f"ERROR: {ROOT} 디렉터리를 찾을 수 없습니다.")
        return

    files = [
        f for f in ROOT.rglob("*.html")
        if "백업" not in str(f) and "복사본" not in str(f)
    ]
    total = len(files)
    print(f"CBT 시험 파일 {total:,}개 스캔 시작...\n")

    counts: dict[str, int] = {
        "modified":    0,
        "already_done": 0,
        "no_body_tag": 0,
        "empty":       0,
        "error":       0,
    }
    errors: list[tuple[Path, str]] = []

    for i, p in enumerate(files, 1):
        status, info = fix_file(p)
        counts[status] = counts.get(status, 0) + 1
        if status == "error":
            errors.append((p, info))
        if i % 2000 == 0:
            print(
                f"  ... {i:,}/{total:,} | "
                f"modified={counts['modified']:,}  "
                f"done={counts['already_done']:,}  "
                f"err={counts['error']}"
            )

    print()
    print("=" * 60)
    print(f"완료. {total:,}개 파일 처리.")
    for k in ("modified", "already_done", "no_body_tag", "empty", "error"):
        print(f"  {k:15s}: {counts.get(k, 0):,}")

    if errors:
        print(f"\n오류 파일 (최대 20개):")
        for p, e in errors[:20]:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
