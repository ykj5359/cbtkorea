#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ERP-인사-2급-실무 폴더의 HTML 파일에서
세로선 CSS 규칙 확인 및 중복 제거
"""

import sys
import re
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

test_file = Path("CBT/ERP-인사-2급-실무/ki20150124.html")

if test_file.exists():
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # .row.text-dark::after 패턴 찾기
    pattern = r'\.row\.text-dark[^{]*::after[^}]*\}'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    print(f"파일: {test_file.name}")
    print(f".row.text-dark::after 규칙 발견: {len(matches)}개")
    print()
    
    for i, match in enumerate(matches, 1):
        start = match.start()
        # 줄 번호 계산
        line_num = content[:start].count('\n') + 1
        print(f"=== 규칙 {i} (줄 {line_num}) ===")
        print(match.group()[:300])
        print()
