"""
rename_main.py — 'CBT KOREA' → 'CBT 기출문제'
대상: 루트 페이지 + CBT-list/*.html + cbt-auth.js / cbt-exam.js (헤더 주석)
(시험 파일 14k는 rename_exam.py 에서 print 버튼 제거와 함께 처리)
"""
from pathlib import Path

ROOT = Path(r"E:\00.CBT")
OLD, NEW = "CBT KOREA", "CBT 기출문제"

roots = ["index.html", "notice.html", "videos.html", "exams.html",
         "community.html", "mypage.html", "cbt-qnet.html", "login.html",
         "signup.html", "cbt-exam-sim.html", "cbt-auth.js", "cbt-exam.js"]
files = [ROOT / r for r in roots] + sorted((ROOT / "CBT-list").glob("*.html"))

changed = 0
total = 0
for p in files:
    if not p.exists():
        continue
    raw = p.read_bytes()
    try:
        text = raw.decode("utf-8"); enc = "utf-8"
    except UnicodeDecodeError:
        text = raw.decode("cp949"); enc = "cp949"
    c = text.count(OLD)
    if c:
        p.write_bytes(text.replace(OLD, NEW).encode(enc))
        changed += 1; total += c

print(f"변경 파일: {changed:,}개 / 치환: {total:,}건")
