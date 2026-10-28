# -*- coding: utf-8 -*-
"""
seo_optimize_exams.py — 기출문제 페이지 구글 검색 최적화 (멱등, 마커 <!-- SEO-OPT-1 -->)
=========================================================================================
1) 존재하지 않는 구 사이트 리소스(cbtkorea.kr/js·theme·css …) <script>/<link> 제거 → 매 방문 404 요청 제거
   + 그 리소스에 의존하던 font_resize 호출 제거, .navbar null 오류 방지
2) 동작하지 않는 숨김 댓글폼(.reply-component)·오류신고 모달(.report-modal)·로딩바(.loading) 제거 → HTML 경량화
3) 제목을 <h1>으로(시험명·회차), 팝업 제목 <h1> → <h5>
4) 페이지 소개문(종목·회차·문항수·과목) + 이전/다음 회차·전체 회차·자격증 가이드 내부 링크
5) BreadcrumbList 구조화 데이터(JSON-LD), 불필요한 keywords 메타 제거, og:image 주소 정정
"""
from __future__ import annotations
import html, json, re, sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(r"E:\00.CBT")
BASE = "https://cbtkorea.kr/"
MARK = "<!-- SEO-OPT-1 -->"

LEGACY_TAG = re.compile(
    r'(?:<!--\s*)?<(?:script|link)\b[^>]*(?:src|href)="https://(?:www\.)?cbtkorea\.kr/(?:js|theme|css)/[^"]*"[^>]*>(?:\s*</script>)?(?:\s*-->)?[ \t]*\r?\n?')
FONT_RESIZE = re.compile(
    r'<script>\s*\$\(function\(\)\s*\{\s*//[^\n]*\n\s*font_resize\([^;]*\);\s*\}\);\s*</script>\s*', re.S)
KEYWORDS = re.compile(r'<meta content="[^"]*" name="keywords"\s*/?>\s*')
CAT_SPAN = re.compile(r'<span class="category-title-text">\s*(.*?)\s*\((\d{4}-\d{2}-\d{2}) 기출문제\)\s*</span>', re.S)
MODAL_H1 = re.compile(r'<h1 (class="modal-title[^"]*"[^>]*)>(.*?)</h1>', re.S)
SUBJ = re.compile(r'<div class="row exam-class-title">\s*<div class="col">\s*<p class="text-center text-dark">\s*(.*?)\s*</p>', re.S)
DATE_IN_NAME = re.compile(r'(\d{8})\.html$')

CSS = MARK + """
<style>
h1.category-title-text{margin:0;line-height:1.4}
.exam-intro{background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;margin:0 0 18px;font-size:14px;line-height:1.8;color:#374151}
.exam-intro p{margin:0 0 6px}
.exam-intro nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.exam-intro nav a{display:inline-block;padding:4px 12px;border:1px solid #d1d5db;border-radius:999px;color:#1d4ed8;text-decoration:none;background:#fff;font-size:13px}
.exam-intro nav a:hover{background:#eff6ff}
</style>
"""


def remove_div_blocks(text: str, cls: str) -> tuple[str, int]:
    """<div class="cls"> … 짝이 맞는 </div> 까지 통째로 제거"""
    opener = f'<div class="{cls}">'
    out, i, n = [], 0, 0
    tag = re.compile(r'<div\b|</div>')
    while True:
        s = text.find(opener, i)
        if s < 0:
            out.append(text[i:]); break
        out.append(text[i:s])
        depth, j = 0, len(text)
        for m in tag.finditer(text, s):
            depth += -1 if m.group() == '</div>' else 1
            if depth == 0:
                j = m.end(); break
        while j < len(text) and text[j] in "\r\n":
            j += 1
        i = j; n += 1
    return "".join(out), n


def dec(b: bytes):
    try:
        return b.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return b.decode("cp949"), "cp949"


def nice_date(d: str) -> str:
    y, m, dd = d.split("-")
    return f"{int(y)}년 {int(m)}월 {int(dd)}일"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    guides = {p.name[:-len("-가이드.html")] for p in (ROOT / "guide").glob("*-가이드.html")}
    st = dict(done=0, skip=0, nocat=0, legacy=0, blocks=0)
    dirs = [d for d in (ROOT / "CBT").iterdir() if d.is_dir() and "백업" not in d.name and "복사본" not in d.name]
    if len(sys.argv) > 1:
        dirs = [d for d in dirs if d.name in sys.argv[1:]]
    for d in sorted(dirs):
        files = sorted((p for p in d.glob("*.html") if "복사본" not in p.name and p.stat().st_size > 0),
                       key=lambda p: (DATE_IN_NAME.search(p.name).group(1) if DATE_IN_NAME.search(p.name) else p.name))
        for idx, p in enumerate(files):
            t, enc = dec(p.read_bytes())
            if MARK in t:
                st["skip"] += 1; continue
            m = CAT_SPAN.search(t)
            if not m:
                st["nocat"] += 1; continue
            name, date = m.group(1).strip(), m.group(2)
            n = t
            n, k = LEGACY_TAG.subn("", n); st["legacy"] += k
            n = FONT_RESIZE.sub("", n)
            n = n.replace("navbar_height = document.querySelector('.navbar').offsetHeight;",
                          "var _nb = document.querySelector('.navbar'); navbar_height = _nb ? _nb.offsetHeight : 0;")
            for cls in ("reply-component", "report-modal", "loading"):
                n, k = remove_div_blocks(n, cls); st["blocks"] += k
            n = KEYWORDS.sub("", n)
            n = n.replace('content="https://www.cbtkorea.kr/img/', 'content="https://cbtkorea.kr/img/')
            n = MODAL_H1.sub(r'<h5 \1>\2</h5>', n)
            n = CAT_SPAN.sub(lambda mm: f'<h1 class="category-title-text">{mm.group(1).strip()} ({mm.group(2)} 기출문제)</h1>', n, count=1)

            # 소개문 + 내부 링크
            qn = n.count('class="col-12 col-sm-12 col-md-6 exam-box')
            subjects = [s for s in (re.sub(r"^\d+과목\s*:\s*", "", s).strip() for s in SUBJ.findall(n)) if not re.search(r"구분", s)]
            cat_enc = quote(d.name)
            links = []
            if idx > 0:
                prev = files[idx-1]
                pm = DATE_IN_NAME.search(prev.name)
                ptxt = f"{pm.group(1)[:4]}-{pm.group(1)[4:6]}-{pm.group(1)[6:]}" if pm else "이전"
                links.append(f'<a href="{quote(prev.name)}" rel="prev">← 이전 회차 ({ptxt})</a>')
            if idx < len(files) - 1:
                nxt = files[idx+1]
                nm = DATE_IN_NAME.search(nxt.name)
                ntxt = f"{nm.group(1)[:4]}-{nm.group(1)[4:6]}-{nm.group(1)[6:]}" if nm else "다음"
                links.append(f'<a href="{quote(nxt.name)}" rel="next">다음 회차 ({ntxt}) →</a>')
            links.append(f'<a href="../../CBT-list/{cat_enc}-list.html">{html.escape(name)} 전체 회차 목록 ({len(files)}회)</a>')
            if d.name in guides:
                links.append(f'<a href="../../guide/{quote(d.name)}-가이드.html">{html.escape(name)} 시험 가이드</a>')
            subj_txt = f" 출제 과목은 {html.escape(' · '.join(subjects))}입니다." if subjects else ""
            intro = (f'<div class="exam-intro"><p><strong>{html.escape(name)}</strong> {nice_date(date)} 시행 필기 기출문제입니다. '
                     f'총 {qn}문항이 수록되어 있으며{"," if subjects else "."}{subj_txt} '
                     f'보기를 선택하면 정답 여부를 바로 확인할 수 있고, [해설] 버튼으로 문항별 해설을, [채점] 버튼으로 점수를 확인할 수 있습니다.</p>'
                     f'<nav aria-label="회차 이동">{"".join(links)}</nav></div>\n')
            anchor = '<div class="row">\n<div class="exams col-12'
            pos = n.find(anchor)
            if pos < 0:
                anchor = '<div class="row">\r\n<div class="exams col-12'
                pos = n.find(anchor)
            if pos >= 0:
                n = n[:pos] + intro + n[pos:]

            url = f"{BASE}CBT/{cat_enc}/{quote(p.name)}"
            crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "CBT 기출문제", "item": BASE},
                {"@type": "ListItem", "position": 2, "name": "기출문제", "item": BASE + "exams.html"},
                {"@type": "ListItem", "position": 3, "name": name, "item": f"{BASE}CBT-list/{cat_enc}-list.html"},
                {"@type": "ListItem", "position": 4, "name": f"{name} {date} 기출문제", "item": url}]}
            ld = '<script type="application/ld+json">' + json.dumps(crumbs, ensure_ascii=False) + "</script>\n"
            n = n.replace("</head>", CSS + ld + "</head>", 1)
            p.write_bytes(n.encode(enc))
            st["done"] += 1
            if st["done"] % 2000 == 0:
                print(f"  {st['done']:,} …", flush=True)
    print(st)


if __name__ == "__main__":
    main()
