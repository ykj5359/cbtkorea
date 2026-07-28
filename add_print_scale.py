"""
Add a `@media print` rule that scales the page to 70% when printing.

Approach:
  - Inject a small <style> block right before </head> (idempotent: if a marker
    comment is already present we skip the file so re-runs don't duplicate).
  - Uses both `zoom` (Chrome/Edge/Safari print) and `transform` fallback.

Idempotency marker:  /* CBT-PRINT-SCALE-V1 */
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")

PRINT_BLOCK = """\
<style>/* CBT-PRINT-SCALE-V1 */
@media print {
    html { zoom: 0.7; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    @page { size: A4; margin: 10mm; }
    /* hide top navigation/buttons that aren't needed when printed */
    .main-buttons, nav, footer, .ad-border { display: none !important; }
}
</style>
"""

MARKER = "/* CBT-PRINT-SCALE-V1 */"
HEAD_END_RE = re.compile(r"</head\s*>", re.IGNORECASE)


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

    if MARKER in text:
        return "already_applied", {}

    m = HEAD_END_RE.search(text)
    if not m:
        return "no_head", {}

    new_text = text[:m.start()] + PRINT_BLOCK + text[m.start():]

    try:
        path.write_bytes(new_text.encode(enc))
    except Exception as e:
        return "error", {"error": f"write: {e}"}

    return "modified", {}


def main():
    if not ROOT.exists():
        print(f"ERROR: {ROOT} not found")
        return

    files = list(ROOT.rglob("*.html"))
    files = [f for f in files if "백업" not in str(f) and "복사본" not in str(f)]
    print(f"Scanning {len(files)} HTML files under {ROOT}")
    print()

    counts: dict[str, int] = {"modified": 0, "already_applied": 0,
                              "no_head": 0, "empty": 0, "error": 0}
    errors: list[tuple[Path, str]] = []

    for i, p in enumerate(files, 1):
        status, info = fix_file(p)
        counts[status] = counts.get(status, 0) + 1
        if status == "error":
            errors.append((p, info.get("error", "?")))
        if i % 2000 == 0:
            print(f"  ... {i}/{len(files)} processed | modified={counts['modified']} "
                  f"already={counts['already_applied']} no_head={counts['no_head']} "
                  f"err={counts['error']}")

    print()
    print("=" * 60)
    print(f"Done. {len(files)} files scanned.")
    for k in ("modified", "already_applied", "no_head", "empty", "error"):
        print(f"  {k:18s} : {counts[k]}")
    if errors:
        print(f"\n{len(errors)} errors (first 20):")
        for p, e in errors[:20]:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
