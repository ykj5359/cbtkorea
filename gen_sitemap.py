# -*- coding: utf-8 -*-
"""
gen_sitemap.py — 전체 사이트 sitemap 생성 (대형 사이트용 인덱스 구조)
================================================================
· sitemap.xml            → 사이트맵 인덱스 (하위 3개 참조)
· sitemap-pages.xml      → 주요 페이지 (홈/기출/공지/커뮤니티 등)
· sitemap-categories.xml → CBT-list 종목 목록 페이지 (약 546개)
· sitemap-exams.xml      → CBT 기출문제 전체 페이지 (약 14,000개)
URL 은 퍼센트 인코딩(한글/괄호) 하여 구글 크롤러가 정확히 인식하도록 함.
"""
from __future__ import annotations
import datetime as dt
from pathlib import Path
from urllib.parse import quote

ROOT = Path(r"E:\00.CBT")
BASE = "https://cbtkorea.kr/"
TODAY = dt.date.today().strftime("%Y-%m-%d")


def skip(p: Path) -> bool:
    s = str(p)
    return "백업" in s or "복사본" in s


def enc(relpath: str) -> str:
    """루트 기준 상대경로를 URL 로 (슬래시 유지, 나머지 인코딩)"""
    return BASE + quote(relpath.replace("\\", "/"), safe="/")


def url_block(loc, changefreq, priority, lastmod=TODAY):
    return (f"  <url>\n    <loc>{loc}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n  </url>\n")


def write_urlset(path: Path, body: str):
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + body + '</urlset>\n', encoding="utf-8")


# ── 1) 주요 페이지 ──
PAGES = [
    ("", "daily", "1.0"),               # 홈 (루트)
    ("exams.html", "weekly", "0.8"),
    ("guides.html", "weekly", "0.9"),
    ("cbt-qnet.html", "weekly", "0.8"),
    ("videos.html", "weekly", "0.6"),
    ("notice.html", "weekly", "0.6"),
    ("community.html", "daily", "0.6"),
    ("about.html", "monthly", "0.7"),
    ("contact.html", "monthly", "0.5"),
    ("privacy.html", "monthly", "0.5"),
    ("terms.html", "monthly", "0.5"),
]
pages_body = "".join(url_block(BASE + f, cf, pr) for f, cf, pr in PAGES)
# 자격증 가이드 페이지 (원본 콘텐츠 — 높은 우선순위)
for f in sorted((ROOT / "guide").glob("*.html")):
    if not skip(f):
        pages_body += url_block(enc("guide/" + f.name), "monthly", "0.8")
write_urlset(ROOT / "sitemap-pages.xml", pages_body)

# ── 2) CBT-list 종목 목록 ──
list_files = sorted(f for f in (ROOT / "CBT-list").glob("*.html") if not skip(f))
cat_body = "".join(url_block(enc("CBT-list/" + f.name), "weekly", "0.7") for f in list_files)
write_urlset(ROOT / "sitemap-categories.xml", cat_body)

# ── 3) CBT 기출문제 전체 ──
exam_files = [f for f in (ROOT / "CBT").rglob("*.html") if not skip(f)]
exam_files.sort()
exam_body = "".join(
    url_block(enc("CBT/" + f.relative_to(ROOT / "CBT").as_posix()), "monthly", "0.6")
    for f in exam_files)
write_urlset(ROOT / "sitemap-exams.xml", exam_body)

# ── 4) 사이트맵 인덱스 ──
idx = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
for name in ("sitemap-pages.xml", "sitemap-categories.xml", "sitemap-exams.xml"):
    idx += f"  <sitemap>\n    <loc>{BASE}{name}</loc>\n    <lastmod>{TODAY}</lastmod>\n  </sitemap>\n"
idx += "</sitemapindex>\n"
(ROOT / "sitemap.xml").write_text(idx, encoding="utf-8")

print(f"주요 페이지: {len(PAGES)}")
print(f"종목 목록:   {len(list_files):,}")
print(f"기출문제:    {len(exam_files):,}")
print(f"→ sitemap.xml(인덱스) + 3개 하위 사이트맵 생성 완료")
