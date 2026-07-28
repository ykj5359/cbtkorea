#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
사회복지사 폴더의 HTML 파일에서
가운데 부분에 중복된 줄(2-3개)을 1개로 수정
"""

import sys
import re
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def find_and_fix_duplicate_lines(content):
    """중복된 줄을 찾아서 1개로 수정"""
    lines = content.splitlines(True)  # keepends=True
    total_lines = len(lines)
    
    if total_lines < 100:
        return content, False  # 파일이 너무 작으면 처리하지 않음
    
    # 중간 부분 확인 (전체의 30% ~ 70% 구간)
    start_check = int(total_lines * 0.3)
    end_check = int(total_lines * 0.7)
    
    new_lines = lines[:start_check]  # 앞부분은 그대로
    modified = False
    
    i = start_check
    while i < end_check:
        # 연속된 동일한 줄 찾기 (2개 이상)
        current_line = lines[i].rstrip('\n\r')
        if not current_line.strip():  # 빈 줄은 그대로 유지
            new_lines.append(lines[i])
            i += 1
            continue
        
        # 연속된 동일한 줄의 개수 확인
        duplicate_count = 1
        j = i + 1
        while j < end_check and j < len(lines):
            next_line = lines[j].rstrip('\n\r')
            if next_line == current_line:
                duplicate_count += 1
                j += 1
            else:
                break
        
        # 중복된 줄이 2개 이상이면 1개만 남김
        if duplicate_count >= 2:
            new_lines.append(lines[i])  # 첫 번째 줄만 추가
            i = j  # 다음 위치로 이동
            modified = True
        else:
            new_lines.append(lines[i])
            i += 1
    
    # 나머지 부분 추가
    new_lines.extend(lines[end_check:])
    
    new_content = ''.join(new_lines)
    return new_content, modified


def process_file(file_path, dry_run=False):
    """단일 파일 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_content, modified = find_and_fix_duplicate_lines(content)
        
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
    print("사회복지사 폴더 중복 줄 제거")
    print("가운데 부분(30%~70% 구간)의 연속된 동일 줄을 1개로 수정")
    print("=" * 60)
    print()
    
    # 사회복지사 폴더 찾기
    cbt_folder = Path("CBT")
    if not cbt_folder.exists():
        print("❌ CBT 폴더를 찾을 수 없습니다.")
        return
    
    social_folders = list(cbt_folder.glob("사회복지사*"))
    
    if not social_folders:
        print("❌ 사회복지사 폴더를 찾을 수 없습니다.")
        return
    
    html_files = []
    for folder in social_folders:
        html_files.extend(list(folder.rglob("*.html")))
    
    # 백업 폴더 제외
    html_files = [f for f in html_files if '백업' not in str(f)]
    
    print(f"📁 사회복지사 폴더: {len(social_folders)}개")
    print(f"📁 총 {len(html_files)}개의 HTML 파일을 찾았습니다.")
    print()
    
    # Dry run 먼저 실행 (처음 5개만 테스트)
    print("=" * 60)
    print("1단계: DRY RUN (처음 5개 파일 테스트)")
    print("=" * 60)
    
    modified_count = 0
    for file_path in html_files[:5]:
        if process_file(file_path, dry_run=True):
            print(f"✅ {file_path.relative_to(cbt_folder)} - 수정 필요")
            modified_count += 1
        else:
            print(f"⏭️  {file_path.relative_to(cbt_folder)} - 변경사항 없음")
    
    print()
    print(f"📊 DRY RUN 결과 (처음 5개): {modified_count}/5개 파일 수정 필요")
    print()
    
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
                print(f"✅ [{i}/{len(html_files)}] {file_path.relative_to(cbt_folder)} - 수정 완료")
                success_count += 1
            else:
                skip_count += 1
                if i % 10 == 0 or i <= 5:
                    print(f"⏭️  [{i}/{len(html_files)}] {file_path.relative_to(cbt_folder)} - 변경사항 없음")
        except Exception as e:
            error_count += 1
            print(f"❌ [{i}/{len(html_files)}] {file_path.relative_to(cbt_folder)} - 오류: {e}")
    
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
