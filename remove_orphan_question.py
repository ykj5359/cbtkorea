"""
Remove orphan 자체검사 question (nj20030316-1) that was accidentally appended
to ERP/DIAT exam files. The orphan belongs to 건설안전기사 (nj20030316) only.

For each affected file (NOT in 건설안전기사 folder):
  - Locate the `<div class_="row text-dark">` row wrapping
    `<div ... id="#nj20030316-1" ...>` (the orphan exam-box)
  - Compute the matching close of that row by counting open/close <div> tags
  - Delete the whole row block

Safety:
  - Skip everything under 건설안전기사/ — those files legitimately reference
    nj20030316-1 because nj20030316 IS the 건설안전기사 file.
  - Only delete if id matches `#nj20030316-1` (very specific orphan signature).
  - Only delete one orphan per file.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")
SKIP_FOLDERS = {"건설안전기사", "백업"}

# Match the row wrapper that opens with class_= (typo) right before the orphan id
ORPHAN_START_RE = re.compile(
    r'<div\s+class_="row text-dark"\s*>\s*'
    r'<div[^>]*id="#nj20030316-1"',
)

# For depth counting, we need a regex to match any <div ...> or </div>
TAG_RE = re.compile(r'<(/?)div\b[^>]*>')


def find_row_end(text: str, row_start: int) -> int:
    """
    Given the position of `<div class_="row text-dark">` at `row_start`,
    return the position one past the matching `</div>` that closes that row.
    Uses simple div-depth counting from the row_start.
    """
    depth = 0
    pos = row_start
    for m in TAG_RE.finditer(text, row_start):
        is_close = m.group(1) == '/'
        if is_close:
            depth -= 1
            if depth == 0:
                return m.end()
        else:
            depth += 1
    return -1  # unbalanced


def fix_file(path: Path) -> tuple[str, dict]:
    # Skip files under unwanted folders
    parts = set(path.parts)
    if parts & SKIP_FOLDERS:
        return "skipped_folder", {}

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

    m = ORPHAN_START_RE.search(text)
    if not m:
        return "no_orphan", {}

    row_start = m.start()
    row_end = find_row_end(text, row_start)
    if row_end == -1:
        return "error", {"error": "div balance failed"}

    # Defensive: orphan block size should be roughly 3000~8000 chars
    block_size = row_end - row_start
    if block_size < 500 or block_size > 30000:
        return "error", {"error": f"unexpected block size {block_size}"}

    new_text = text[:row_start] + text[row_end:]

    try:
        path.write_bytes(new_text.encode(enc))
    except Exception as e:
        return "error", {"error": f"write: {e}"}

    return "modified", {"removed_chars": block_size, "row_start": row_start}


def main():
    if not ROOT.exists():
        print(f"ERROR: {ROOT} not found")
        return

    files = list(ROOT.rglob("*.html"))
    files = [f for f in files if "백업" not in str(f) and "복사본" not in str(f)]
    print(f"Scanning {len(files)} HTML files under {ROOT}")
    print()

    counts: dict[str, int] = {"modified": 0, "no_orphan": 0, "empty": 0,
                              "skipped_folder": 0, "error": 0}
    errors: list[tuple[Path, str]] = []
    examples: list[Path] = []

    for i, p in enumerate(files, 1):
        status, info = fix_file(p)
        counts[status] = counts.get(status, 0) + 1
        if status == "modified" and len(examples) < 5:
            examples.append(p)
        if status == "error":
            errors.append((p, info.get("error", "?")))
        if i % 2000 == 0:
            print(f"  ... {i}/{len(files)} processed | modified={counts['modified']} "
                  f"no_orphan={counts['no_orphan']} skipped={counts['skipped_folder']} "
                  f"err={counts['error']}")

    print()
    print("=" * 60)
    print(f"Done. {len(files)} files scanned.")
    for k in ("modified", "no_orphan", "empty", "skipped_folder", "error"):
        print(f"  {k:18s} : {counts[k]}")
    if examples:
        print("\nSample modified files:")
        for p in examples:
            print(f"  {p}")
    if errors:
        print(f"\n{len(errors)} errors (first 20):")
        for p, e in errors[:20]:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
