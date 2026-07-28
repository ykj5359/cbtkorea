"""
Improve the vertical divider CSS to render as ONE perfectly-centered, clearly
visible line across all browsers/zoom levels.

Background:
  Earlier fix moved the divider from per-row `.row.text-dark::after` to a single
  `.exams::after` using `right: 50%`. In some long pages (e.g. 농산물품질관리사
  with 100 questions and embedded images), the percent-based right offset can
  appear to jitter slightly, looking like overlapping segments.

Fix:
  - Use `left: 50%; margin-left: -0.5px;` for sub-pixel-accurate centering.
  - Slightly darker color (#d1d5db) so the line is unambiguously visible.
  - z-index: 0 so it sits behind content without competing with question text.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")

# Match the current .exams::after block (as produced by fix_vertical_divider.py)
OLD_RE = re.compile(
    r"\.exams::after\s*\{\s*\n"
    r"\s*content:\s*'';\s*\n"
    r"\s*position:\s*absolute;\s*\n"
    r"\s*top:\s*0;\s*\n"
    r"\s*right:\s*50%;\s*\n"
    r"\s*bottom:\s*0;\s*\n"
    r"\s*width:\s*1px;\s*\n"
    r"\s*background-color:\s*#e5e7eb;\s*\n"
    r"\s*z-index:\s*1;\s*\n"
    r"\s*pointer-events:\s*none;\s*\n"
    r"\s*\}"
)

NEW_BLOCK = (
    ".exams::after {\n"
    "        content: '';\n"
    "        position: absolute;\n"
    "        top: 0;\n"
    "        bottom: 0;\n"
    "        left: 50%;\n"
    "        margin-left: -0.5px;\n"
    "        width: 1px;\n"
    "        background-color: #d1d5db;\n"
    "        z-index: 0;\n"
    "        pointer-events: none;\n"
    "    }"
)


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

    new_text, n = OLD_RE.subn(NEW_BLOCK, text)
    if n == 0:
        return "no_pattern", {}

    try:
        path.write_bytes(new_text.encode(enc))
    except Exception as e:
        return "error", {"error": f"write: {e}"}

    return "modified", {"replacements": n}


def main():
    if not ROOT.exists():
        print(f"ERROR: {ROOT} not found")
        return

    files = list(ROOT.rglob("*.html"))
    files = [f for f in files if "백업" not in str(f) and "복사본" not in str(f)]
    print(f"Scanning {len(files)} HTML files under {ROOT}")
    print()

    counts: dict[str, int] = {"modified": 0, "no_pattern": 0, "empty": 0, "error": 0}
    errors: list[tuple[Path, str]] = []

    for i, p in enumerate(files, 1):
        status, info = fix_file(p)
        counts[status] = counts.get(status, 0) + 1
        if status == "error":
            errors.append((p, info.get("error", "?")))
        if i % 2000 == 0:
            print(f"  ... {i}/{len(files)} processed | modified={counts['modified']} "
                  f"no_pattern={counts['no_pattern']} err={counts['error']}")

    print()
    print("=" * 60)
    print(f"Done. {len(files)} files scanned.")
    for k in ("modified", "no_pattern", "empty", "error"):
        print(f"  {k:12s} : {counts[k]}")
    if errors:
        print(f"\n{len(errors)} errors (first 20):")
        for p, e in errors[:20]:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
