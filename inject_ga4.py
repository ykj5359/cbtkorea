# -*- coding: utf-8 -*-
"""inject_ga4.py — 전 페이지 GA4(G-C6X67SNW5B) 적용, 타인 소유 GA/GTM 제거. 멱등(<!-- GA4-CBT --> 마커)."""
import re, sys
from pathlib import Path
ROOT = Path(r"E:\00.CBT"); GA = "G-C6X67SNW5B"; MARK = "<!-- GA4-CBT -->"
SNIP = (MARK + '\n<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
        "gtag('js',new Date());gtag('config','%s');</script>\n<!-- /GA4-CBT -->\n" % (GA, GA))
GTM = re.compile(r"<!-- Google Tag Manager -->.*?<!-- End Google Tag Manager -->\s*", re.S)
GTM_NS = re.compile(r"<!-- Google Tag Manager \(noscript\) -->.*?<!-- End Google Tag Manager \(noscript\) -->\s*", re.S)
OLDGA = re.compile(r'<!-- Google tag \(gtag\.js\) -->\s*<script[^>]*G-D1VJBM7447[^>]*></script>\s*<script>.*?</script>\s*', re.S)
HEAD = re.compile(r"<head[^>]*>", re.I)

def dec(b):
    try: return b.decode("utf-8"), "utf-8"
    except UnicodeDecodeError: return b.decode("cp949"), "cp949"

def main():
    files = [p for p in ROOT.glob("*.html")] + [p for d in ("CBT", "CBT-list", "guide") for p in (ROOT/d).rglob("*.html")]
    files = [p for p in files if "백업" not in str(p) and "복사본" not in str(p) and not p.name.startswith("google")]
    st = {"done": 0, "skip": 0, "nohead": 0, "empty": 0}
    for p in files:
        b = p.read_bytes()
        if not b: st["empty"] += 1; continue
        t, enc = dec(b)
        if MARK in t: st["skip"] += 1; continue
        n = GTM.sub("", t); n = GTM_NS.sub("", n); n = OLDGA.sub("", n)
        m = HEAD.search(n)
        if not m: st["nohead"] += 1; continue
        n = n[:m.end()] + "\n" + SNIP + n[m.end():]
        p.write_bytes(n.encode(enc)); st["done"] += 1
    print(len(files), st)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); main()
