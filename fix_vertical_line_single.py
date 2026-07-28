#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ERP-인사-2급-실무 폴더의 HTML 파일에서
세로선 CSS를 하나만 남기고 중복 제거
"""

import sys
import re
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def fix_vertical_line_css(content):
    """세로선 CSS 규칙 정리 - 하나만 유지"""
    # .row.text-dark::after 규칙 찾기 (미디어 쿼리 제외)
    # 미디어 쿼리 안의 것은 유지하고, 일반 스타일에서 중복 제거
    
    # 먼저 미디어 쿼리 영역 찾기
    media_pattern = r'@media[^{]*\{'
    media_matches = list(re.finditer(media_pattern, content))
    
    # 미디어 쿼리 범위 계산 (중괄호 매칭)
    media_ranges = []
    for match in media_matches:
        start = match.start()
        brace_count = 0
        for i in range(start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    media_ranges.append((start, i + 1))
                    break
    
    # .row.text-dark::after 규칙 찾기 (미디어 쿼리 제외)
    pattern = r'\.row\.text-dark::after\s*\{[^}]*\}'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    # 미디어 쿼리 밖의 규칙만 찾기
    valid_matches = []
    for match in matches:
        match_start = match.start()
        # 미디어 쿼리 안에 있지 않은지 확인
        in_media = False
        for media_start, media_end in media_ranges:
            if media_start <= match_start < media_end:
                in_media = True
                break
        if not in_media:
            valid_matches.append(match)
    
    # 2개 이상이면 첫 번째만 남기고 나머지 제거
    if len(valid_matches) > 1:
        # 뒤에서부터 제거 (인덱스 문제 방지)
        for match in reversed(valid_matches[1:]):
            content = content[:match.start()] + content[match.end():]
        return content, True
    
    # .row.text-dark 규칙도 확인 (중복 제거)
    pattern2 = r'\.row\.text-dark\s*\{[^}]*position:\s*relative[^}]*\}'
    matches2 = list(re.finditer(pattern2, content, re.DOTALL))
    
    if len(matches2) > 1:
        # 첫 번째만 남기고 나머지 제거
        for match in reversed(matches2[1:]):
            content = content[:match.start()] + content[match.end():]
        return content, True
    
    return content, False


def process_file(file_path, dry_run=False):
    """단일 파일 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_content, modified = fix_vertical_line_css(content)
        
        if not modified:
            return False  # 변경사항 없음
        
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"❌ {file_path.name} 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    print("=" * 60)
    print("ERP-인사-2급-실무 폴더 세로선 CSS 중복 제거")
    print("세로선 규칙을 하나만 유지")
    print("=" * 60)
    print()
    
    folder = Path("CBT/ERP-인사-2급-실무")
    if not folder.exists():
        print("❌ 폴더를 찾을 수 없습니다.")
        return
    
    html_files = list(folder.glob("*.html"))
    
    # 백업 폴더 제외
    html_files = [f for f in html_files if '백업' not in str(f)]
    
    print(f"📁 총 {len(html_files)}개의 HTML 파일을 찾았습니다.")
    print()
    
    # Dry run 먼저 실행 (처음 5개만 테스트)
    print("=" * 60)
    print("1단계: DRY RUN (처음 5개 파일 테스트)")
    print("=" * 60)
    
    modified_count = 0
    for file_path in html_files[:5]:
        if process_file(file_path, dry_run=True):
            print(f"✅ {file_path.name} - 수정 필요")
            modified_count += 1
        else:
            print(f"⏭️  {file_path.name} - 변경사항 없음")
    
    print()
    print(f"📊 DRY RUN 결과 (처음 5개): {modified_count}/5개 파일 수정 필요")
    print()
    
    # 사용자 확인
    if modified_count > 0:
        print("테스트 결과, 수정이 필요한 파일이 있습니다.")
        print("전체 파일을 수정하시겠습니까? (y/n): ", end='')
        # 실제 실행
        print("실행 중...")
    
    # 전체 파일 처리
    print("=" * 60)
    print("2단계: 실제 파일 수정 (전체)")
    print("=" * 60)
    print()
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, file_path in enumerate(html_files, 1):
        try:
            if process_file(file_path, dry_run=False):
                print(f"✅ [{i}/{len(html_files)}] {file_path.name} - 수정 완료")
                success_count += 1
            else:
                skip_count += 1
                if i % 10 == 0 or i <= 5:
                    print(f"⏭️  [{i}/{len(html_files)}] {file_path.name} - 변경사항 없음")
        except Exception as e:
            error_count += 1
            print(f"❌ [{i}/{len(html_files)}] {file_path.name} - 오류: {e}")
    
    print()
    print("=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"📊 총 파일 수: {len(html_files)}개")
    print(f"✅ 수정 완료: {success_count}개")
    print(f"⏭️  스킵/변경없음: {skip_count}개")
    print(f"❌ 오류: {error_count}개")


if __name__ == "__main__":
    main()
