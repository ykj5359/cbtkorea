"""
Add the missing "정답/체크/해설" button row to the LAST question of each exam file.

Background:
  In every CBT/<exam>/<code>.html the last question is consistently missing the
  bottom action button row (정답/체크/해설). All other questions in the same file
  have one. This script detects the missing row and inserts it.

Detection:
  - Find all `question-num="N"` occurrences -> identify the last question.
  - Slice the file from "last question start" to the `<!-- 하단 시작` marker
    (footer/wrap-up section). This slice represents the last question's body.
  - If `exam-buttons text-center` already appears in that slice, skip the file.

Insertion:
  - Insert the standard button row immediately before the `<!-- 하단 시작` marker.
  - HTML is forgiving with div nesting; visual placement matches working files.

Standard button row (taken verbatim from working files):
  <div class="row"><div class="col-12 exam-buttons text-center">
    <button class="correct-number btn btn-outline-secondary" type="button">정답</button>
    <button class="chk-question btn btn-outline-secondary" type="button">체크</button>
    <button class="show-comment btn btn-outline-secondary" type="button">해설</button>
  </div></div>
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")

BUTTON_ROW = (
    '<div class="row"><div class="col-12 exam-buttons text-center">'
    '<button class="correct-number btn btn-outline-secondary" type="button">정답</button>'
    '<button class="chk-question btn btn-outline-secondary" type="button">체크</button>'
    '<button class="show-comment btn btn-outline-secondary" type="button">해설</button>'
    '</div></div>'
)

RE_Q_NUM = re.compile(r'question-num="(\d+)"')
FOOTER_MARKERS = ("<!-- 하단 시작", "<footer")


def find_footer_marker(text: str, after_pos: int) -> int:
    """Return earliest occurrence of any known footer marker after `after_pos`, or -1."""
    best = -1
    for m in FOOTER_MARKERS:
        i = text.find(m, after_pos)
        if i != -1 and (best == -1 or i < best):
            best = i
    return best


def fix_file(path: Path) -> tuple[str, dict]:
    """
    Returns:
      status: 'modified' | 'already_ok' | 'no_questions' | 'no_footer' | 'error'
      info:   {'last_q': int, 'inserted_at': int, 'error': str}
    """
    try:
        raw = path.read_bytes()
    except Exception as e:
        return "error", {"error": f"read failed: {e}"}

    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949")
            enc = "cp949"
        except UnicodeDecodeError:
            return "error", {"error": "decode failed (utf-8/cp949)"}

    # 1) Find last question
    qnum_matches = list(RE_Q_NUM.finditer(text))
    if not qnum_matches:
        return "no_questions", {}

    last_match = qnum_matches[-1]
    last_q = int(last_match.group(1))
    last_q_pos = last_match.start()

    # 2) Find footer marker after last question
    footer_pos = find_footer_marker(text, last_q_pos)
    if footer_pos == -1:
        return "no_footer", {"last_q": last_q}

    # 3) Check if last question already has the button row
    slice_after_last_q = text[last_q_pos:footer_pos]
    if "exam-buttons text-center" in slice_after_last_q:
        return "already_ok", {"last_q": last_q}

    # 4) Insert button row right before footer marker
    new_text = text[:footer_pos] + BUTTON_ROW + "\n" + text[footer_pos:]

    try:
        path.write_bytes(new_text.encode(enc))
    except Exception as e:
        return "error", {"error": f"write failed: {e}"}

    return "modified", {"last_q": last_q, "inserted_at": footer_pos}


def main():
    if not ROOT.exists():
        print(f"ERROR: {ROOT} not found")
        return

    files = list(ROOT.rglob("*.html"))
    files = [f for f in files if "백업" not in str(f) and "복사본" not in str(f)]
    print(f"Scanning {len(files)} HTML files under {ROOT}")
    print()

    counts = {
        "modified": 0,
        "already_ok": 0,
        "no_questions": 0,
        "no_footer": 0,
        "error": 0,
    }
    errors: list[tuple[Path, str]] = []

    for i, p in enumerate(files, 1):
        status, info = fix_file(p)
        counts[status] = counts.get(status, 0) + 1
        if status == "error":
            errors.append((p, info.get("error", "?")))
        if i % 1000 == 0:
            print(f"  ... {i}/{len(files)} processed | "
                  f"modified={counts['modified']} ok={counts['already_ok']} "
                  f"no_q={counts['no_questions']} no_footer={counts['no_footer']} "
                  f"err={counts['error']}")

    print()
    print("=" * 60)
    print(f"Done. {len(files)} files scanned.")
    print(f"  modified            : {counts['modified']}")
    print(f"  already had buttons : {counts['already_ok']}")
    print(f"  no question found   : {counts['no_questions']}")
    print(f"  no footer marker    : {counts['no_footer']}")
    print(f"  errors              : {counts['error']}")
    if errors:
        print("\nFirst 20 errors:")
        for p, e in errors[:20]:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
