"""
Fix the <title> and og:title meta tag of every exam HTML file so the print
header and browser tab show the correct exam name (not a leftover template).

Source of truth:
  - Folder name = exam subject (kept verbatim per user's example like
    '농산물품질관리사-1차 (2022-04-02 기출문제)')
  - Date = the last 8 consecutive digits in the filename, parsed as YYYYMMDD.

Final format (matches the user's example):
  '{folder_name} ({YYYY-MM-DD} 기출문제)'

What gets updated:
  - <title>...</title>
  - <meta property="og:title" content="...">  (and the content="..." variant)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")

# Pull the last YYYYMMDD block from a filename like xyz20140222.html
DATE_RE = re.compile(r"(\d{8})\.html?$", re.IGNORECASE)

TITLE_RE = re.compile(r"<title>[^<]*</title>", re.IGNORECASE)
# Meta og:title with either property/content ordering
OG_TITLE_RE_1 = re.compile(
    r'(<meta[^>]*\bproperty\s*=\s*"og:title"[^>]*\bcontent\s*=\s*")[^"]*(")',
    re.IGNORECASE,
)
OG_TITLE_RE_2 = re.compile(
    r'(<meta[^>]*\bcontent\s*=\s*")[^"]*("\s*[^>]*\bproperty\s*=\s*"og:title")',
    re.IGNORECASE,
)


def derive_title(path: Path) -> str | None:
    """folder + date → '폴더명 (YYYY-MM-DD 기출문제)'. Returns None if no date."""
    m = DATE_RE.search(path.name)
    if not m:
        return None
    ymd = m.group(1)
    yr, mo, dy = ymd[:4], ymd[4:6], ymd[6:8]
    # Validate roughly
    if not (1990 <= int(yr) <= 2099 and 1 <= int(mo) <= 12 and 1 <= int(dy) <= 31):
        return None
    folder = path.parent.name  # e.g. "ERP-인사-2급-이론"
    return f"{folder} ({yr}-{mo}-{dy} 기출문제)"


def fix_file(path: Path) -> tuple[str, dict]:
    new_title = derive_title(path)
    if new_title is None:
        return "no_date", {}

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

    original = text
    n_title = 0
    n_og = 0

    new_text, c = TITLE_RE.subn(f"<title>{new_title}</title>", text)
    n_title = c
    text = new_text

    new_text, c = OG_TITLE_RE_1.subn(rf"\g<1>{new_title}\g<2>", text)
    n_og += c
    text = new_text

    new_text, c = OG_TITLE_RE_2.subn(rf"\g<1>{new_title}\g<2>", text)
    n_og += c
    text = new_text

    if text == original:
        return "no_change", {}

    try:
        path.write_bytes(text.encode(enc))
    except Exception as e:
        return "error", {"error": f"write: {e}"}

    return "modified", {"title_updates": n_title, "og_updates": n_og, "new_title": new_title}


def main():
    if not ROOT.exists():
        print(f"ERROR: {ROOT} not found")
        return

    files = list(ROOT.rglob("*.html"))
    files = [f for f in files if "백업" not in str(f) and "복사본" not in str(f)]
    print(f"Scanning {len(files)} HTML files under {ROOT}")
    print()

    counts: dict[str, int] = {"modified": 0, "no_change": 0, "no_date": 0,
                              "empty": 0, "error": 0}
    sample_titles: list[str] = []
    errors: list[tuple[Path, str]] = []

    for i, p in enumerate(files, 1):
        status, info = fix_file(p)
        counts[status] = counts.get(status, 0) + 1
        if status == "modified" and len(sample_titles) < 5:
            sample_titles.append(info["new_title"])
        if status == "error":
            errors.append((p, info.get("error", "?")))
        if i % 2000 == 0:
            print(f"  ... {i}/{len(files)} processed | modified={counts['modified']} "
                  f"no_change={counts['no_change']} no_date={counts['no_date']} "
                  f"err={counts['error']}")

    print()
    print("=" * 60)
    print(f"Done. {len(files)} files scanned.")
    for k in ("modified", "no_change", "no_date", "empty", "error"):
        print(f"  {k:12s} : {counts[k]}")
    if sample_titles:
        print("\nSample new titles:")
        for t in sample_titles:
            print(f"  {t}")
    if errors:
        print(f"\n{len(errors)} errors (first 20):")
        for p, e in errors[:20]:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
