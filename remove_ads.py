"""
Remove Google AdSense scripts from all CBT HTML files.

Targets:
  1. <script ... googlesyndication.com/.../adsbygoogle.js ...></script>
  2. <div class="ad-border"> ... </div>   (ad container blocks)
  3. Stray <ins class="adsbygoogle" ...></ins> (if not wrapped by ad-border)
  4. Stray inline <script> ... adsbygoogle.push({}) ... </script>

Does NOT touch:
  - CSS rules like `.ad-border { ... }` (those are inside <style>, not as <div class=...>)
  - Anything outside the patterns above
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"E:\00.CBT")

# 1) Loader script (whole <script ...></script> on possibly one line)
RE_LOADER = re.compile(
    r'<script[^>]*\bsrc\s*=\s*"[^"]*googlesyndication\.com[^"]*"[^>]*>\s*</script>\s*',
    re.IGNORECASE,
)

# 2) Ad container <div class="ad-border"> ... </div> (non-greedy, DOTALL)
RE_ADBORDER = re.compile(
    r'<div\s+class="ad-border"\s*>.*?</div>\s*',
    re.IGNORECASE | re.DOTALL,
)

# 3) Stray <ins class="adsbygoogle" ...></ins>
RE_INS = re.compile(
    r'<ins\s+class="adsbygoogle"[^>]*>\s*</ins>\s*',
    re.IGNORECASE,
)

# 4) Stray inline <script>...adsbygoogle.push...</script>
RE_PUSH_SCRIPT = re.compile(
    r'<script[^>]*>\s*\(?adsbygoogle\s*=.*?adsbygoogle\.push\([^)]*\)\s*;?\s*</script>\s*',
    re.IGNORECASE | re.DOTALL,
)


def clean_file(path: Path) -> tuple[bool, dict]:
    try:
        raw = path.read_bytes()
    except Exception as e:
        return False, {"error": str(e)}

    # Try UTF-8 first, then fall back to cp949 (some old files)
    enc = "utf-8"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949")
            enc = "cp949"
        except UnicodeDecodeError:
            return False, {"error": "decode failed"}

    original = text
    counts = {"loader": 0, "adborder": 0, "ins": 0, "push": 0}

    text, n = RE_ADBORDER.subn("", text)
    counts["adborder"] = n
    text, n = RE_LOADER.subn("", text)
    counts["loader"] = n
    text, n = RE_INS.subn("", text)
    counts["ins"] = n
    text, n = RE_PUSH_SCRIPT.subn("", text)
    counts["push"] = n

    if text == original:
        return False, counts

    # Write back in the same encoding to preserve any non-utf8 bytes
    path.write_bytes(text.encode(enc))
    return True, counts


def main():
    html_files = list(ROOT.rglob("*.html"))
    print(f"Scanning {len(html_files)} HTML files under {ROOT}")

    modified = 0
    totals = {"loader": 0, "adborder": 0, "ins": 0, "push": 0}
    errors = []

    for i, p in enumerate(html_files, 1):
        changed, info = clean_file(p)
        if "error" in info:
            errors.append((p, info["error"]))
            continue
        if changed:
            modified += 1
            for k in totals:
                totals[k] += info[k]
        if i % 500 == 0:
            print(f"  ... {i}/{len(html_files)} processed, {modified} modified so far")

    print()
    print(f"Done. {modified} files modified out of {len(html_files)}.")
    print(f"Removed: loader={totals['loader']}, ad-border blocks={totals['adborder']}, "
          f"stray <ins>={totals['ins']}, stray push scripts={totals['push']}")
    if errors:
        print(f"\n{len(errors)} files had errors:")
        for p, e in errors[:20]:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
