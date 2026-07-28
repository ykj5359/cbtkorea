"""
recolor_qnet.py — Q-Net(뀨-Net) 관련 보라/인디고 색상을 녹색(emerald) 계열로 치환.
대상: cbt-auth.js, cbt-exam.js, cbt-qnet.html, index.html
(보라 계열 hex/rgba/violet-클래스는 Q-Net 테마 전용이라 다른 요소에 영향 없음)
"""
from pathlib import Path

ROOT = Path(r"E:\00.CBT")
FILES = ["cbt-auth.js", "cbt-exam.js", "cbt-qnet.html", "index.html"]

REPL = [
    # 보라/인디고 hex → emerald 계열
    ("#7c3aed", "#059669"),
    ("#6d28d9", "#047857"),
    ("#4f46e5", "#047857"),
    ("#5b21b6", "#047857"),
    ("#4c1d95", "#065f46"),
    ("#2e1065", "#064e3b"),
    ("#8b5cf6", "#34d399"),
    ("#a78bfa", "#6ee7b7"),
    ("#ede9fe", "#d1fae5"),
    ("#f5f2ff", "#ecfdf5"),
    ("#f0ebff", "#ecfdf5"),
    ("#f6f4ff", "#f2fbf6"),
    # rgba 보라 그림자 → emerald 그림자
    ("rgba(99,70,237", "rgba(5,150,105"),
    ("rgba(124,58,237", "rgba(5,150,105"),
    ("rgba(99, 70, 237", "rgba(5, 150, 105"),
    ("rgba(124, 58, 237", "rgba(5, 150, 105"),
    # 히어로 광채(청록/핑크) → 녹색톤
    ("rgba(34,211,238,.18)", "rgba(16,185,129,.20)"),
    ("rgba(236,72,153,.16)", "rgba(52,211,153,.16)"),
    # Tailwind violet 클래스 (violet은 Q-Net 전용)
    ("text-violet-100", "text-emerald-100"),
    ("text-violet-600", "text-emerald-600"),
    ("bg-violet-50", "bg-emerald-50"),
    ("focus:border-violet-400", "focus:border-emerald-400"),
    ("focus:ring-violet-100", "focus:ring-emerald-100"),
]


def main():
    for name in FILES:
        p = ROOT / name
        raw = p.read_bytes()
        try:
            text = raw.decode("utf-8"); enc = "utf-8"
        except UnicodeDecodeError:
            text = raw.decode("cp949"); enc = "cp949"
        n = 0
        for a, b in REPL:
            c = text.count(a)
            if c:
                text = text.replace(a, b); n += c
        p.write_bytes(text.encode(enc))
        print(f"  {name}: {n}건 치환")


if __name__ == "__main__":
    main()
