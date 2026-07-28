"""Test single-file fix on bx20060305.html WITHOUT writing back."""
from pathlib import Path
from add_last_exam_buttons import (
    RE_Q_NUM, BUTTON_ROW, find_footer_marker
)

TEST = Path(r"E:\00.CBT\CBT\용접산업기사\bx20060305.html")

text = TEST.read_text(encoding="utf-8")
print(f"File size: {len(text):,} chars")

qs = list(RE_Q_NUM.finditer(text))
print(f"Total question-num occurrences: {len(qs)}")
last = qs[-1]
print(f"Last question num: {last.group(1)} at offset {last.start()}")

footer_pos = find_footer_marker(text, last.start())
print(f"Footer marker at offset: {footer_pos}")

slice_after = text[last.start():footer_pos]
has_buttons = "exam-buttons text-center" in slice_after
print(f"Last question already has buttons: {has_buttons}")

if not has_buttons:
    print("\n--- Tail BEFORE insertion (last 300 chars before footer marker) ---")
    print(text[max(0, footer_pos-300):footer_pos])

    new_text = text[:footer_pos] + BUTTON_ROW + "\n" + text[footer_pos:]
    print("\n--- Tail AFTER insertion (300 chars around footer marker) ---")
    new_footer = new_text.find("<!-- 하단 시작")
    print(new_text[max(0, new_footer-len(BUTTON_ROW)-50):new_footer+100])
    print(f"\nDelta: +{len(new_text)-len(text)} chars")
