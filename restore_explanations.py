# -*- coding: utf-8 -*-
"""
restore_explanations.py — 시험 페이지 해설(AI 참고 해설) 복원
=================================================================
remove_fake_comments.py 가 비운 <ul class="view-reply"> 에, 로컬 백업
(D:\CBT백업\00.CBT\CBT, 같은 상대경로)의 해설 본문만 꺼내 깔끔한 블록으로 다시 넣는다.
· 가짜 닉네임/날짜/좋아요/오류신고 버튼은 복원하지 않음 (본문만)
· AI 작성분은 "AI 참고 해설", 그 외는 "이용자 해설" 라벨
· 빈 상자에 보이던 report-modal '확인' 버튼 숨김 CSS 추가
멱등: 마커 <!-- AI-EXP-RESTORED --> 가 있는 파일은 건너뜀.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(r"E:\00.CBT")
BACKUP = Path(r"D:\CBT백업\00.CBT\CBT")   # 2026-04 로컬 원본 백업 (해설 포함)
MARKER = "<!-- AI-EXP-RESTORED -->"
AI_NICKS = {"CBT 기출문제AI", "CBT문제은행AI", "CBT KOREA AI", "CBTKOREA AI"}

OPEN_UL = '<ul class="view-reply">'
EMPTY_UL = '<ul class="view-reply"></ul>'
ITEM_RE = re.compile(
    r'<li class="reply-item[^"]*" data-info="[^"]*exam_id:([^",]+)"(.*?)</li>', re.S)
NICK_RE = re.compile(r'class="nick">([^<]*)<')
COMMENT_RE = re.compile(r'<div class="reply-comment">(.*?)</div><div class="btn-toolbar', re.S)
QID_RE = re.compile(r'question-id="([^"]+)"')

STYLE = MARKER + """
<style>
    .reply .report-modal, .reply .loading, .reply .reply-component { display: none !important; }
    .ai-exp { list-style: none; padding: 0; margin: 0 0 10px 0; }
    .ai-exp:last-child { margin-bottom: 0; }
    .ai-exp-label { font-size: 12px; font-weight: 700; color: #1d4ed8; margin-bottom: 6px; }
    .ai-exp-label small { font-weight: 400; color: #6b7280; margin-left: 6px; }
    .ai-exp-empty { font-size: 13px; color: #6b7280; }
</style>
"""


def extract_old(text: str) -> dict[str, list[tuple[str, str]]]:
    """옛 HTML → {exam_id: [(nick, comment_html), ...]}"""
    out: dict[str, list[tuple[str, str]]] = {}
    for m in ITEM_RE.finditer(text):
        exam_id, body = m.group(1), m.group(2)
        nk = NICK_RE.search(body)
        cm = COMMENT_RE.search(body)
        if not cm:
            continue
        html = cm.group(1).strip()
        if not re.sub(r"<[^>]+>|&nbsp;|\s", "", html):
            continue
        out.setdefault(exam_id, []).append((nk.group(1).strip() if nk else "", html))
    return out


def build_ul(items: list[tuple[str, str]]) -> str:
    if not items:
        return ('<ul class="view-reply"><li class="ai-exp">'
                '<div class="ai-exp-empty">이 문항은 아직 해설이 준비되지 않았습니다.</div></li></ul>')
    lis = []
    for nick, html in items:
        if nick in AI_NICKS or nick.endswith("AI"):
            label = 'AI 참고 해설<small>자동 생성된 해설이므로 오류가 있을 수 있습니다</small>'
        else:
            label = '이용자 해설'
        lis.append(f'<li class="ai-exp"><div class="ai-exp-label">{label}</div>'
                   f'<div class="reply-comment">{html}</div></li>')
    return '<ul class="view-reply">' + "".join(lis) + '</ul>'


def restore(cur: str, old_map: dict) -> tuple[str, int, int]:
    """현재 HTML의 빈 view-reply 를 문항 순서대로 채운다. (새 HTML, 채운 수, 해설 없음 수)"""
    qids = QID_RE.findall(cur)
    parts = cur.split(EMPTY_UL)
    if len(parts) - 1 != len(qids):
        raise ValueError(f"문항 {len(qids)} vs 빈 해설칸 {len(parts)-1} 불일치")
    filled = missing = 0
    out = [parts[0]]
    for qid, nxt in zip(qids, parts[1:]):
        items = old_map.get(qid, [])
        if items:
            filled += 1
        else:
            missing += 1
        out.append(build_ul(items))
        out.append(nxt)
    new = "".join(out)
    new = new.replace("</head>", STYLE + "</head>", 1)
    return new, filled, missing


def decode(raw: bytes) -> tuple[str, str]:
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp949"), "cp949"


def main():
    """로컬 백업(D:\\CBT백업\\00.CBT\\CBT)의 같은 경로 파일에서 해설을 가져온다."""
    stats = {"modified": 0, "skip_marker": 0, "no_empty": 0, "mismatch": 0,
             "no_backup": 0, "error": 0, "filled": 0, "noexp": 0}
    n = 0
    cur_files = [p for p in (ROOT / "CBT").rglob("*.html")
                 if "백업" not in str(p) and "복사본" not in str(p)]
    print(f"현재 페이지 {len(cur_files):,}개, 백업 소스: {BACKUP}", flush=True)
    missing_list = []
    for cur_path in cur_files:
        name = cur_path.relative_to(ROOT).as_posix()
        old_path = BACKUP / cur_path.relative_to(ROOT / "CBT")
        n += 1
        try:
            cur_text, enc = decode(cur_path.read_bytes())
            if MARKER in cur_text:
                stats["skip_marker"] += 1
                continue
            if not old_path.exists():
                stats["no_backup"] += 1
                missing_list.append(name)
                continue
            old_text, _ = decode(old_path.read_bytes())
            if MARKER in cur_text:
                stats["skip_marker"] += 1
                continue
            if EMPTY_UL not in cur_text:
                stats["no_empty"] += 1
                continue
            old_map = extract_old(old_text)
            new, filled, missing = restore(cur_text, old_map)
            cur_path.write_bytes(new.encode(enc))
            stats["modified"] += 1
            stats["filled"] += filled
            stats["noexp"] += missing
        except ValueError as e:
            stats["mismatch"] += 1
            if stats["mismatch"] <= 5:
                print("  불일치:", name, e)
        except Exception as e:
            stats["error"] += 1
            if stats["error"] <= 5:
                print("  오류:", name, repr(e))
        if n % 2000 == 0:
            print(f"  {n:,} 처리...", flush=True)
    print(f"처리 {n:,}개 →", stats)
    if missing_list:
        (ROOT / "restore_explanations_missing.log").write_text("\n".join(missing_list), encoding="utf-8")
        print(f"백업에 없는 파일 {len(missing_list)}개 → restore_explanations_missing.log")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
