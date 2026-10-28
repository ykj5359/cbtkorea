# -*- coding: utf-8 -*-
"""fix_exam_titles.py — 기출문제 페이지 제목/OG/설명 정정 + 홈을 가리키는 잘못된 canonical 제거 (멱등)
원본 템플릿 잔재: 모든 페이지 <title>이 '건설안전기사 필기 기출문제복원 (2003-03-16)'로 동일했고,
<link href="https://www.cbtkorea.kr" rel="canonical"/> 이 self canonical 과 충돌하고 있었음."""
import re, sys, html
from pathlib import Path
from urllib.parse import quote
ROOT = Path(r"E:\00.CBT")
CAT_RX = re.compile(r'<span class="category-title-text">\s*(.*?)\s*\((\d{4}-\d{2}-\d{2}) 기출문제\)\s*</span>', re.S)
BAD_CANON = re.compile(r'<link href="https://www\.cbtkorea\.kr/?" rel="canonical"\s*/?>\s*')

def dec(b):
    try: return b.decode("utf-8"), "utf-8"
    except UnicodeDecodeError: return b.decode("cp949"), "cp949"

def main():
    st = {"title": 0, "canon": 0, "nocat": 0, "files": 0}
    for p in (ROOT / "CBT").rglob("*.html"):
        s = str(p)
        if "백업" in s or "복사본" in s: continue
        b = p.read_bytes()
        if not b: continue
        t, enc = dec(b); n = t; st["files"] += 1
        n, k = BAD_CANON.subn("", n); st["canon"] += bool(k)
        m = CAT_RX.search(n)
        if m and "건설안전기사 필기 기출문제복원 (2003-03-16)" in n or (m and "DIAT 정보통신상식 필기 기출문제복원 (2003-03-16)" in n):
            name, date = m.group(1).strip(), m.group(2)
            title = f"{name} 필기 기출문제 ({date}) - CBT 기출문제"
            desc = f"{name} {date} 기출문제 무료 CBT 문제풀이. 정답 확인, 해설, 채점, 오답노트를 제공합니다."
            url = f"https://cbtkorea.kr/CBT/{quote(p.parent.name)}/{quote(p.name)}"
            et, ed = html.escape(title, quote=True), html.escape(desc, quote=True)
            n = re.sub(r"<title>.*?</title>", f"<title>{et}</title>", n, count=1, flags=re.S)
            n = re.sub(r'<meta content="[^"]*" property="og:title"\s*/?>', f'<meta content="{et}" property="og:title"/>', n, count=1)
            n = re.sub(r'<meta content="[^"]*" property="og:url"\s*/?>', f'<meta content="{url}" property="og:url"/>', n, count=1)
            n = re.sub(r'<meta content="[^"]*" name="description"\s*/?>', f'<meta content="{ed}" name="description"/>', n, count=1)
            n = re.sub(r'<meta content="[^"]*" property="og:description"\s*/?>', f'<meta content="{ed}" property="og:description"/>', n, count=1)
            js = title.replace("\\", "\\\\").replace("'", "\'")
            n = n.replace("'DIAT 정보통신상식 필기 기출문제복원 (2003-03-16) - CBT 기출문제'", f"'{js}'")
            n = n.replace("'title': 'DIAT 정보통신상식 (2003-03-16)'", "'title': '" + f"{name} ({date})".replace("'", "\'") + "'")
            st["title"] += 1
        elif not m:
            st["nocat"] += 1
        if n != t: p.write_bytes(n.encode(enc))
    print(st)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); main()
