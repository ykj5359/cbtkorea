# -*- coding: utf-8 -*-
"""
build_loan_broker.py — 대출중개인(대출성 상품 판매대리·중개업자) 자격인증평가 문제 → CBT 페이지 생성
================================================================================================
입력: loan.json (PDF '대출중개인 자격시험.pdf' 43~92쪽 문제·정답·해설 파싱 결과, 279문항/48단원)
출력: CBT/대출중개인-자격시험/loan01~04.html (평가과목별 4개) + CBT-list/대출중개인-자격시험-list.html
템플릿: 기존 기출 페이지(문항 마크업/채점/해설 버튼/북마크 등 공용 스크립트 그대로 사용)
※ 국가자격이 아니므로 실전 CBT(cbt-qnet-data.js)에는 넣지 않음.
"""
from __future__ import annotations
import copy, html, json, re, sys
from pathlib import Path
from urllib.parse import quote
from bs4 import BeautifulSoup

ROOT = Path(r"E:\00.CBT")
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "loan.json"
TEMPLATE = ROOT / "CBT" / "건설기계설비산업기사" / "mx20200606.html"
CAT = "대출중개인-자격시험"
CAT_NAME = "대출중개인 자격시험"
FULL_NAME = "대출성 상품 판매대리·중개업자 자격인증평가"
SRC_LABEL = "대출중개인 자격인증평가 문제집 해설"

SUBJECTS = [  # (파일, 평가과목, 단원 범위)
    ("loan01", "금융기초", range(1, 8)),
    ("loan02", "금융소비자보호", range(8, 18)),
    ("loan03", "금융상품", range(18, 32)),
    ("loan04", "고객관리", range(32, 49)),
]


def text_html(s: str) -> str:
    return "<br/>".join(html.escape(x.strip()) for x in s.split("\n") if x.strip())


def build_box(proto, qid, num, q, a, side):
    box = copy.copy(proto)
    box["class"] = [c for c in box["class"] if c not in ("exam-left", "exam-right")] + [side]
    box["id"] = "#" + qid
    box["question-id"] = qid
    box["question-num"] = str(num)
    title = box.select_one("p.exam-title")
    title.clear()
    title.append(BeautifulSoup(f'<span class="exam-number">{num}</span>. {text_html(q["q"])}', "html.parser"))
    ol = box.select_one("ol.circlednumbers")
    ox = a["a"] in ("O", "X")
    opts = ["O (맞다)", "X (틀리다)"] if ox else q["opts"]
    correct = (1 if a["a"] == "O" else 2) if ox else int(a["a"])
    ol["correct"] = str(correct)
    ol.clear()
    for i, o in enumerate(opts, 1):
        li = BeautifulSoup(f"<li>{text_html(o)}</li>", "html.parser").li
        if i == correct:
            li["class"] = "correct"
        ol.append(li)
    ul = box.select_one("ul.view-reply")
    ul.clear()
    exp = a["exp"].strip() or "해설이 제공되지 않은 문항입니다."
    ul.append(BeautifulSoup(
        f'<li class="ai-exp"><div class="ai-exp-label">해설<small>{SRC_LABEL}</small></div>'
        f'<div class="reply-comment">정답: {"O" if ox and correct == 1 else "X" if ox else "①②③④"[correct-1]}<br/>{html.escape(exp)}</div></li>',
        "html.parser"))
    for inp in box.select("input.exam_id"):
        inp["value"] = qid
    return box


def build_page(tpl_text, data, fname, subj, chapters, idx, total):
    soup = BeautifulSoup(tpl_text, "html.parser")
    exams = soup.select_one("div.exams")
    proto = copy.copy(exams.select_one("div.exam-box"))
    title_proto = copy.copy(exams.select_one("div.exam-class-title"))
    exams.clear()
    num = 0
    for ch in chapters:
        keys = [k for k in data["q"] if int(k.split("-")[0]) == ch]
        keys.sort(key=lambda k: int(k.split("-")[1]))
        t = copy.copy(title_proto)
        t.select_one("p").string = f"{ch}단원: {data['titles'][str(ch)].rstrip('*')}"
        exams.append(t)
        row = None
        for i, k in enumerate(keys):
            num += 1
            if i % 2 == 0:
                row = soup.new_tag("div", attrs={"class": "row text-dark"})
                exams.append(row)
            row.append(build_box(proto, f"{fname}-{num}", num, data["q"][k], data["a"][k],
                                 "exam-left" if i % 2 == 0 else "exam-right"))
    page_title = f"{CAT_NAME} {subj} 단원별 문제 ({idx}/{total}) - CBT 기출문제"
    desc = f"{FULL_NAME} {subj} 과목 단원별 문제 {num}문항 무료 CBT 문제풀이 - 정답·해설·채점 제공"
    out = str(soup)
    url = f"https://cbtkorea.kr/CBT/{quote(CAT)}/{fname}.html"
    out = re.sub(r"<title>.*?</title>", f"<title>{html.escape(page_title)}</title>", out, count=1, flags=re.S)
    out = re.sub(r'<meta content="[^"]*" property="og:title"/>', f'<meta content="{html.escape(page_title)}" property="og:title"/>', out)
    out = re.sub(r'<meta content="[^"]*" property="og:url"/>', f'<meta content="{url}" property="og:url"/>', out)
    out = re.sub(r'<meta content="[^"]*" name="description"/>', f'<meta content="{html.escape(desc)}" name="description"/>', out)
    out = re.sub(r'<meta content="[^"]*" property="og:description"/>', f'<meta content="{html.escape(desc)}" property="og:description"/>', out)
    out = re.sub(r'<link href="[^"]*" rel="canonical"/>|<link rel="canonical" href="[^"]*">',
                 f'<link rel="canonical" href="{url}">', out)
    out = re.sub(r'<span class="category-title-text">.*?</span>',
                 f'<span class="category-title-text">{CAT_NAME} ({subj} · {num}문항)</span>', out, count=1, flags=re.S)
    out = out.replace("../../CBT-list/건설기계설비산업기사-list.html", f"../../CBT-list/{CAT}-list.html")
    # 국가자격이 아니므로 실전 CBT 모드 진입 버튼 숨김
    out = out.replace("</head>", "<style>#cbt-fab-cbt{display:none!important}</style>\n</head>", 1)
    assert "mx20200606" not in out, "템플릿 잔재"
    return out, num


def build_list(counts):
    tpl = (ROOT / "CBT-list" / "ERP-회계-2급-이론-list.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(tpl, "html.parser")
    links = soup.select('a[href^="../CBT/"]')
    container = links[0].parent
    proto = copy.copy(links[0])
    for a in links:
        a.decompose()
    for (fname, subj, chs), n in zip(SUBJECTS, counts):
        a = copy.copy(proto)
        a["href"] = f"../CBT/{CAT}/{fname}.html"
        a.select_one("p").string = f"{subj} 단원별 문제 ({chs.start}~{chs.stop-1}단원 · {n}문항)"
        container.append(a)
    out = str(soup).replace("ERP-회계-2급-이론", CAT).replace("ERP 회계 2급 이론", CAT_NAME)
    out = re.sub(r"총 \d+개의 기출문제가 있습니다\.", f"총 {len(SUBJECTS)}개 과목, {sum(counts)}문항이 있습니다.", out)
    out = out.replace(f"{CAT_NAME} 기출문제 목록", f"{CAT_NAME} 문제 목록")
    out = out.replace(quote("ERP-회계-2급-이론"), quote(CAT))
    note = (f'<p class="text-sm text-gray-600 mb-4">{FULL_NAME}(금융소비자보호법에 따른 민간 자격인증평가, '
            f'평가과목: 금융기초·금융소비자보호·금융상품·고객관리, 50문항·90분·60점 이상 합격) 대비 단원별 문제입니다. '
            f'국가기술자격이 아니므로 실전 CBT 모의시험에는 포함되지 않습니다.</p>')
    soup2 = BeautifulSoup(out, "html.parser")
    first = soup2.select_one(f'a[href^="../CBT/{CAT}/"]')
    first.parent.insert_before(BeautifulSoup(note, "html.parser"))
    return str(soup2)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    tpl = TEMPLATE.read_text(encoding="utf-8")
    outdir = ROOT / "CBT" / CAT
    outdir.mkdir(exist_ok=True)
    counts = []
    for i, (fname, subj, chs) in enumerate(SUBJECTS, 1):
        page, n = build_page(tpl, data, fname, subj, chs, i, len(SUBJECTS))
        (outdir / f"{fname}.html").write_bytes(page.encode("utf-8"))
        counts.append(n)
        print(f"{fname}.html  {subj:8s} {n}문항")
    (ROOT / "CBT-list" / f"{CAT}-list.html").write_bytes(build_list(counts).encode("utf-8"))
    print("목록 페이지 생성, 총", sum(counts), "문항")


if __name__ == "__main__":
    main()
