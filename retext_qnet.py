"""
retext_qnet.py — 네비 메뉴의 'Q-Net CBT 응시' → '뀨-Net CBT'
대상: 루트 페이지 5개 + CBT-list/*.html (546)
(cbt-auth.js가 JS로 교체하는 페이지도 정적 텍스트까지 맞춰 둠)
"""
from pathlib import Path

ROOT = Path(r"E:\00.CBT")
OLD = "Q-Net CBT 응시"
NEW = "뀨-Net CBT"

targets = ["notice.html", "videos.html", "exams.html", "community.html", "mypage.html"]
files = [ROOT / t for t in targets] + sorted((ROOT / "CBT-list").glob("*.html"))

changed = 0
for p in files:
    if not p.exists():
        continue
    raw = p.read_bytes()
    try:
        text = raw.decode("utf-8"); enc = "utf-8"
    except UnicodeDecodeError:
        text = raw.decode("cp949"); enc = "cp949"
    if OLD in text:
        p.write_bytes(text.replace(OLD, NEW).encode(enc))
        changed += 1

print(f"변경된 파일: {changed:,}개")
