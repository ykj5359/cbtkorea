#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
사회복지사 폴더에서 중복된 줄 패턴 찾기
"""

import sys
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 테스트 파일 읽기
test_file = Path("CBT/사회복지사-1급(1교시)/f120140125.html")
if test_file.exists():
    with open(test_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"파일: {test_file.name}")
    print(f"총 줄 수: {len(lines)}")
    print()
    
    # 중간 부분 확인 (3340줄 근처)
    print("3340줄 근처 (3330-3350):")
    for i in range(3329, min(3350, len(lines))):
        line = lines[i].rstrip()
        print(f"{i+1:5d}: {line[:100]}")
    
    print()
    print("="*80)
    print()
    
    # 연속된 동일한 줄 찾기
    print("연속된 동일한 줄 찾기:")
    prev_line = None
    duplicate_count = 0
    for i, line in enumerate(lines):
        line_stripped = line.rstrip()
        if line_stripped and line_stripped == prev_line:
            duplicate_count += 1
            if duplicate_count <= 10:  # 처음 10개만 출력
                print(f"줄 {i}: {line_stripped[:80]}")
                print(f"줄 {i-1}: {prev_line[:80]}")
                print()
        else:
            duplicate_count = 0
        prev_line = line_stripped
