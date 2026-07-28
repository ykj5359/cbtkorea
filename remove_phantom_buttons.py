"""
Remove "phantom" empty exam-right column that contains only the action buttons
without an actual question.

Problem case (example: vv20210515.html):
  After the last real question (Q45 in left column), a previous fix script left
  a placeholder right column whose only content is a 정답/체크/해설 button row:

      <div class="col-12 col-sm-12 col-md-6 exam-box exam-right">
        <div class="row"><div class="col-12">
          <div class="row"><div class="col-12 exam-buttons text-center">
            <button>정답</button><button>체크</button><button>해설</button>
          </div></div>
        </div></div>
      </div>

  This block has NO question text and confuses users. Remove the whole block.

Safety:
  - Only matches the exact phantom structure (5 nested divs, button row, 5 closes).
  - Does NOT touch legitimate exam-right blocks that contain a real question
    (those have <p class="exam-title">, <ol class="circlednumbers">, etc.).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")

# Tight pattern: exam-right opens, then 4 wrapping divs, then exactly the 3-button
# row, then exactly 5 closing divs. No question content can fit inside.
PHANTOM = re.compile(
    r'<div class="col-12 col-sm-12 col-md-6 exam-box exam-right">'
    r'<div class="row"><div class="col-12">'
    r'<div class="row"><div class="col-12 exam-buttons text-center">'
    r'<button class="correct-number[^"]*" type="button">정답</button>'
    r'<button class="chk-question[^"]*" type="button">체크</button>'
    r'<button class="show-comment[^"]*" type="button">해설</button>'
    r'</div></div></div></div></div>'
)


def fix_file(path: Path) -> tuple[str, int]:
    """Returns (status, n_removed)."""
    try:
        raw = path.read_bytes()
    except Exception as e:
        return f"error: read {e}", 0

    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949")
            enc = "cp949"
        except UnicodeDecodeError:
            return "error: decode", 0

    new_text, n = PHANTOM.subn("", text)
    if n == 0:
        return "no_phantom", 0

    try:
        path.write_bytes(new_text.encode(enc))
    except Exception as e:
        return f"error: write {e}", 0

    return "modified", n


def main():
    if not ROOT.exists():
        print(f"ERROR: {ROOT} not found")
        return

    files = list(ROOT.rglob("*.html"))
    files = [f for f in files if "백업" not in str(f) and "복사본" not in str(f)]
    print(f"Scanning {len(files)} HTML files under {ROOT}")
    print()

    modified = 0
    total_removed = 0
    errors: list[tuple[Path, str]] = []

    for i, p in enumerate(files, 1):
        status, n = fix_file(p)
        if status == "modified":
            modified += 1
            total_removed += n
        elif status.startswith("error"):
            errors.append((p, status))
        if i % 1000 == 0:
            print(f"  ... {i}/{len(files)} processed | modified={modified} removed={total_removed}")

    print()
    print("=" * 60)
    print(f"Done. {len(files)} files scanned.")
    print(f"  files modified         : {modified}")
    print(f"  phantom blocks removed : {total_removed}")
    print(f"  errors                 : {len(errors)}")
    if errors:
        print("\nFirst 20 errors:")
        for p, e in errors[:20]:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
