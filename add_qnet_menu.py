"""
add_qnet_menu.py
================
1. 루트 페이지(notice/videos/exams): Q-Net 메뉴 + navAuthArea + cbt-auth.js
2. community/mypage: Q-Net 메뉴만 추가
3. CBT-list/*.html (546개): Q-Net 메뉴 추가

멱등: 이미 cbt-qnet.html 링크가 있으면 건너뜀
실행: python add_qnet_menu.py
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(r"E:\00.CBT")

QNET_ROOT = '<a href="cbt-qnet.html" class="text-black hover:text-gray-700">Q-Net CBT 응시</a>'
QNET_LIST = '<a href="../cbt-qnet.html" class="text-black hover:text-gray-700">Q-Net CBT 응시</a>'

AUTH_AREA = '<div id="navAuthArea" class="flex items-center space-x-4"></div>'
OLD_BTNS_RE = re.compile(
    r'<div class="flex items-center space-x-4">\s*'
    r'<button class="text-sm font-medium text-gray-500 hover:text-gray-700">로그인</button>\s*'
    r'<button class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-blue-700 transition">회원가입</button>\s*'
    r'</div>',
    re.DOTALL)


def read(p: Path):
    raw = p.read_bytes()
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp949"), "cp949"


def write(p: Path, text: str, enc: str):
    p.write_bytes(text.encode(enc))


def insert_after_exams(text: str, exams_href: str, qnet_html: str) -> tuple[str, bool]:
    if 'cbt-qnet.html' in text:
        return text, False
    pat = re.compile(r'(<a href="' + re.escape(exams_href) + r'"[^>]*>기출문제</a>)')
    m = pat.search(text)
    if not m:
        return text, False
    indent = ''
    line_start = text.rfind('\n', 0, m.start()) + 1
    indent = text[line_start:m.start()]
    if indent.strip():
        indent = '                    '
    new = text[:m.end()] + '\n' + indent + qnet_html + text[m.end():]
    return new, True


def fix_root_page(name: str, add_auth: bool):
    p = ROOT / name
    if not p.exists():
        print(f"  SKIP (없음): {name}")
        return
    text, enc = read(p)
    changed = False

    text, ins = insert_after_exams(text, 'exams.html', QNET_ROOT)
    changed |= ins

    if add_auth:
        if 'navAuthArea' not in text:
            text, n = OLD_BTNS_RE.subn(AUTH_AREA, text, count=1)
            changed |= n > 0
        if 'cbt-auth.js' not in text:
            text, n = re.subn(r'</body>', '<script src="cbt-auth.js"></script>\n</body>', text, count=1, flags=re.IGNORECASE)
            changed |= n > 0

    if changed:
        write(p, text, enc)
        print(f"  OK: {name}")
    else:
        print(f"  변경 없음: {name}")


def main():
    print("[루트 페이지]")
    for name in ("notice.html", "videos.html", "exams.html"):
        fix_root_page(name, add_auth=True)
    for name in ("community.html", "mypage.html"):
        fix_root_page(name, add_auth=False)

    print("[CBT-list 페이지]")
    list_dir = ROOT / "CBT-list"
    ok = skip = 0
    for p in sorted(list_dir.glob("*.html")):
        text, enc = read(p)
        text, ins = insert_after_exams(text, '../exams.html', QNET_LIST)
        if ins:
            write(p, text, enc)
            ok += 1
        else:
            skip += 1
    print(f"  수정 {ok:,}개 / 건너뜀 {skip:,}개")


if __name__ == "__main__":
    main()
