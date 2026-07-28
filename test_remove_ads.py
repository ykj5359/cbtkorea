"""Dry-run test: show before/after counts on a single file without writing."""
import re
from pathlib import Path

from remove_ads import RE_LOADER, RE_ADBORDER, RE_INS, RE_PUSH_SCRIPT

TEST_FILE = Path(r"E:\00.CBT\CBT\정보처리기사\iz20220424.html")

text = TEST_FILE.read_text(encoding="utf-8")
orig_len = len(text)

print(f"File: {TEST_FILE}")
print(f"Original size: {orig_len:,} chars")

# Count matches before removal
m_loader = len(RE_LOADER.findall(text))
m_border = len(RE_ADBORDER.findall(text))
m_ins = len(RE_INS.findall(text))
m_push = len(RE_PUSH_SCRIPT.findall(text))

print(f"\nMatches found:")
print(f"  Loader scripts (googlesyndication): {m_loader}")
print(f"  <div class='ad-border'>...</div>:   {m_border}")
print(f"  <ins class='adsbygoogle'>:          {m_ins}")
print(f"  inline adsbygoogle.push scripts:    {m_push}")

# Apply removals
text2 = RE_ADBORDER.sub("", text)
text2 = RE_LOADER.sub("", text2)
text2 = RE_INS.sub("", text2)
text2 = RE_PUSH_SCRIPT.sub("", text2)

print(f"\nAfter removal: {len(text2):,} chars (removed {orig_len - len(text2):,} chars)")

# Sanity: any residual ad references?
residual_ad = len(re.findall(r'adsbygoogle|googlesyndication', text2, re.IGNORECASE))
residual_border = len(re.findall(r'<div\s+class="ad-border"', text2, re.IGNORECASE))
print(f"\nResidual after cleanup:")
print(f"  'adsbygoogle/googlesyndication' references: {residual_ad}")
print(f"  '<div class=\"ad-border\">' remaining:        {residual_border}")

# Show CSS .ad-border still present (must remain)
css_border = len(re.findall(r'\.ad-border\s*[{,]', text2))
print(f"  CSS '.ad-border' rules preserved:            {css_border}")
