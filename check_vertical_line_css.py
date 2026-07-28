#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ERP-회계-2급-이론 폴더의 HTML 파일에서
중복된 세로 구분선 CSS 규칙 확인
"""

import sys
import re
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

test_file = Path("CBT/ERP-회계-2급-이론/kg20140222.html")

if test_file.exists():
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # .row.text-dark::after 패턴 찾기
    pattern1 = r'\.row\.text-dark[^{]*::after[^}]*}'
    matches1 = list(re.finditer(pattern1, content, re.DOTALL))
    
    print(f"파일: {test_file.name}")
    print(f".row.text-dark::after 규칙 발견: {len(matches1)}개")
    print()
    
    for i, match in enumerate(matches1, 1):
        start = match.start()
        end = match.end()
        # 앞뒤 200자 컨텍스트
        context_start = max(0, start - 200)
        context_end = min(len(content), end + 200)
        context = content[context_start:context_end]
        
        # 줄 번호 계산
        line_num = content[:start].count('\n') + 1
        
        print(f"=== 규칙 {i} (줄 {line_num}) ===")
        print(match.group())
        print()
