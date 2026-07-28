"""
gen_qnet_data.py
================
CBT/{종목}/*.html 을 스캔해 cbt-qnet-data.js 생성.
file:// 환경에서 fetch 없이 회차 목록을 읽기 위한 정적 데이터.

출력: E:/00.CBT/cbt-qnet-data.js
    window.CBT_QNET_DATA = { "정보처리기사": [{f:"iz20220424.html", t:"2022년 4월 24일 기출문제"}, ...], ... }

실행: python gen_qnet_data.py
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT\CBT")
OUT  = Path(r"E:\00.CBT\cbt-qnet-data.js")

DATE_RE = re.compile(r'(\d{4})(\d{2})(\d{2})')


def title_for(fname: str) -> tuple[str, str]:
    """파일명 → (표시 제목, 정렬키)"""
    stem = fname[:-5] if fname.lower().endswith(".html") else fname
    m = DATE_RE.search(stem)
    if m:
        y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
        return f"{y}년 {mo}월 {d}일 기출문제", f"{m.group(1)}{m.group(2)}{m.group(3)}"
    return stem, "00000000" + stem


def count_questions(path) -> int:
    """파일 내 문항 수 = question-num=" 등장 횟수 (빠른 바이트 카운트)"""
    try:
        raw = path.read_bytes()
    except Exception:
        return 0
    n = raw.count(b'question-num="')
    if n == 0:
        n = raw.count(b'question-id="')
    return n


def main() -> None:
    data: dict[str, list] = {}
    n_files = 0
    for cat_dir in sorted(ROOT.iterdir()):
        if not cat_dir.is_dir():
            continue
        name = cat_dir.name
        if "백업" in name or "복사본" in name:
            continue
        rounds = []
        for f in cat_dir.glob("*.html"):
            t, key = title_for(f.name)
            n = count_questions(f)
            rounds.append((key, {"f": f.name, "t": t, "n": n}))
        if not rounds:
            continue
        rounds.sort(key=lambda x: x[0], reverse=True)  # 최신순
        data[name] = [r[1] for r in rounds]
        n_files += len(rounds)

    js = ("/* 자동 생성: gen_qnet_data.py — Q-Net CBT 응시 회차 목록 (file:// 지원용) */\n"
          "window.CBT_QNET_DATA = "
          + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
          + ";\n")
    OUT.write_text(js, encoding="utf-8")
    print(f"종목 {len(data):,}개 / 회차 {n_files:,}개 → {OUT} ({OUT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
