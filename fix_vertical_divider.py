"""
Fix the vertical divider between left/right question columns.

Problem:
  Each `.row.text-dark` row draws its OWN `::after` pseudo-element vertical line.
  With 30+ rows stacked, the per-row lines can appear misaligned or as multiple
  overlapping short lines (visible in 손해평가사/ce20190615.html).

Fix:
  Replace per-row vertical-line CSS with ONE single line drawn on the parent
  `.exams` container. The line spans the entire question area uninterrupted.

What this changes:
  1. The CSS block:
         .row.text-dark { position: relative; }
         .row.text-dark::after { ... draws line ... }
     becomes:
         .exams { position: relative; }
         .exams::after { ... draws single line ... pointer-events: none; }
  2. The media query rule `.row.text-dark::after { display: none !important; }`
     gets `.exams::after,` prepended so the new line also hides on mobile.

What this does NOT change:
  - `.row.text-dark { margin-bottom: 20pt !important; }` (unrelated rule, kept)
  - `.exam-class-title .text-dark` (different selector, kept)
  - Any HTML structure
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")

# Old CSS block (with flexible whitespace). The leading indentation is 4 spaces
# in all files we've inspected; we keep that exact pattern.
OLD_CSS = re.compile(
    r"/\* 좌우 구분선 - 얇은 연결된 선 \*/\s*\n"
    r"\s*\.row\.text-dark\s*\{\s*\n"
    r"\s*position:\s*relative;\s*\n"
    r"\s*\}\s*\n"
    r"\s*\.row\.text-dark::after\s*\{\s*\n"
    r"\s*content:\s*'';\s*\n"
    r"\s*position:\s*absolute;\s*\n"
    r"\s*top:\s*0;\s*\n"
    r"\s*right:\s*50%;\s*\n"
    r"\s*bottom:\s*0;\s*\n"
    r"\s*width:\s*1px;\s*\n"
    r"\s*background-color:\s*#e5e7eb;\s*\n"
    r"\s*z-index:\s*1;\s*\n"
    r"\s*\}"
)

NEW_CSS = (
    "/* 좌우 구분선 - 단일 통합 세로선 (.exams 컨테이너에 한 줄만 표시) */\n"
    "    .exams {\n"
    "        position: relative;\n"
    "    }\n"
    "    .exams::after {\n"
    "        content: '';\n"
    "        position: absolute;\n"
    "        top: 0;\n"
    "        right: 50%;\n"
    "        bottom: 0;\n"
    "        width: 1px;\n"
    "        background-color: #e5e7eb;\n"
    "        z-index: 1;\n"
    "        pointer-events: none;\n"
    "    }"
)

# Media-query rule: hide-on-mobile. We want .exams::after also hidden there.
OLD_MQ = re.compile(
    r"(@media\s*\([^)]*max-width[^)]*\)\s*\{\s*\n"
    r"\s*)\.row\.text-dark::after(\s*\{\s*\n"
    r"\s*display:\s*none\s*!important;)"
)
NEW_MQ_REPL = r"\1.exams::after,\n        .row.text-dark::after\2"


def fix_file(path: Path) -> tuple[str, dict]:
    try:
        raw = path.read_bytes()
    except Exception as e:
        return "error", {"error": f"read: {e}"}

    if len(raw) == 0:
        return "empty", {}

    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949")
            enc = "cp949"
        except UnicodeDecodeError:
            return "error", {"error": "decode failed"}

    changed = False

    new_text, n1 = OLD_CSS.subn(NEW_CSS, text)
    if n1 == 0:
        return "no_pattern", {}
    changed = changed or n1 > 0

    new_text, n2 = OLD_MQ.subn(NEW_MQ_REPL, new_text)

    if not changed and n2 == 0:
        return "no_change", {}

    try:
        path.write_bytes(new_text.encode(enc))
    except Exception as e:
        return "error", {"error": f"write: {e}"}

    return "modified", {"main_blocks": n1, "media_blocks": n2}


def main():
    if not ROOT.exists():
        print(f"ERROR: {ROOT} not found")
        return

    files = list(ROOT.rglob("*.html"))
    files = [f for f in files if "백업" not in str(f) and "복사본" not in str(f)]
    print(f"Scanning {len(files)} HTML files under {ROOT}")
    print()

    counts = {"modified": 0, "no_pattern": 0, "empty": 0, "error": 0}
    main_total = 0
    media_total = 0
    errors: list[tuple[Path, str]] = []

    for i, p in enumerate(files, 1):
        status, info = fix_file(p)
        counts[status] = counts.get(status, 0) + 1
        if status == "modified":
            main_total += info["main_blocks"]
            media_total += info["media_blocks"]
        elif status == "error":
            errors.append((p, info["error"]))
        if i % 1000 == 0:
            print(f"  ... {i}/{len(files)} processed | modified={counts['modified']} "
                  f"no_pattern={counts['no_pattern']} empty={counts['empty']} err={counts['error']}")

    print()
    print("=" * 60)
    print(f"Done. {len(files)} files scanned.")
    print(f"  modified              : {counts['modified']}")
    print(f"    main CSS blocks     : {main_total}")
    print(f"    media-query updates : {media_total}")
    print(f"  no pattern found      : {counts['no_pattern']}")
    print(f"  empty files           : {counts['empty']}")
    print(f"  errors                : {counts['error']}")
    if errors:
        print("\nFirst 20 errors:")
        for p, e in errors[:20]:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
