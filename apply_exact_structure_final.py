#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CBT 폴더의 모든 HTML 파일에 기준 파일의 구조를 적용하는 스크립트
- 변경되는 내용: 제목, 문제, 보기, 해설, 이미지 파일 링크 (파일에 맞게)
- 변경되지 않는 내용: 전체적인 스타일, 우측 상단 버튼, 문제 하단 버튼 스타일
기준 파일: CBT/건설안전기사/nj20030316 - 복사본.html
"""

import os
import re
import sys
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 기준 파일 경로
TEMPLATE_FILE = Path("CBT/건설안전기사/nj20030316 - 복사본.html")


def extract_date_from_filename(filename: str) -> str:
    """파일명에서 뒤에서 8자리 숫자를 추출하여 YYYY-MM-DD 형식으로 변환"""
    numbers = re.findall(r'\d+', filename)
    if not numbers:
        return None
    
    last_number = numbers[-1]
    if len(last_number) >= 8:
        date_str = last_number[-8:]
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{year}-{month}-{day}"
    
    return None


def extract_problem_content(content):
    """문제 내용 부분 추출 (<div class="exams"> 부터 </div></div></div></div></div> 까지)"""
    # 문제 시작 부분 찾기
    exams_start = content.find('<div class="exams')
    if exams_start == -1:
        exams_start = content.find('<div class="row">')
        if exams_start != -1:
            # <div class="row"> 다음에 <div class="exams"> 찾기
            temp_start = content.find('<div class="exams', exams_start)
            if temp_start != -1:
                exams_start = content.rfind('<div class="row">', exams_start, temp_start)
    
    if exams_start == -1:
        return None, None
    
    # 문제 끝 부분 찾기 (마지막 </div></div></div></div></div> 전까지)
    # footer 또는 <!-- 하단 시작 --> 전까지
    footer_start = content.find('<!-- 하단 시작', exams_start)
    if footer_start == -1:
        footer_start = content.find('<footer', exams_start)
    if footer_start == -1:
        footer_start = content.rfind('</div></div></div></div></div>', exams_start)
        if footer_start != -1:
            footer_start += len('</div></div></div></div></div>')
    
    if footer_start == -1:
        return None, None
    
    problem_content = content[exams_start:footer_start]
    return problem_content, exams_start


def apply_exact_structure(template_file, target_file, dry_run=False):
    """기준 파일의 구조를 대상 파일에 적용 (2열 구조 유지, 스타일 유지)"""
    try:
        # 기준 파일 읽기
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 대상 파일 읽기
        with open(target_file, 'r', encoding='utf-8') as f:
            target_content = f.read()
        
        original_target = target_content
        
        # 대상 파일에서 문제 내용 추출 (2열 구조 포함)
        problem_content, problem_start = extract_problem_content(target_content)
        
        if problem_content is None:
            # 문제 내용 부분이 없는 파일은 스킵 (목록 파일 등)
            return False
        
        # 기준 파일에서 문제 내용 부분 찾기
        template_problem, template_problem_start = extract_problem_content(template_content)
        
        if template_problem is None:
            print(f"⚠️  {template_file.name}: 문제 내용 부분을 찾을 수 없습니다.")
            return False
        
        # 기준 파일의 헤더 부분 (문제 시작 전까지) - 스타일, 버튼 모두 포함
        template_header = template_content[:template_problem_start]
        
        # 기준 파일의 푸터 부분 (문제 끝난 후)
        template_footer_start = template_content.find('<!-- 하단 시작', template_problem_start)
        if template_footer_start == -1:
            template_footer_start = template_content.find('<footer', template_problem_start)
        if template_footer_start == -1:
            template_footer_start = template_content.rfind('</div></div></div></div></div>', template_problem_start)
            if template_footer_start != -1:
                template_footer_start += len('</div></div></div></div></div>')
        
        if template_footer_start == -1:
            print(f"⚠️  {template_file.name}: 푸터 부분을 찾을 수 없습니다.")
            return False
        
        template_footer = template_content[template_footer_start:]
        
        # 폴더명과 날짜로 제목 생성
        folder_name = target_file.parent.name
        date_str = extract_date_from_filename(target_file.name)
        if date_str:
            new_title = f"{folder_name} ({date_str} 기출문제)"
        else:
            # 날짜를 추출할 수 없으면 기존 제목 유지
            title_match = re.search(r'<span class="category-title-text">(.*?)</span>', target_content)
            if title_match:
                new_title = title_match.group(1)
            else:
                new_title = folder_name
        
        # 기준 파일 헤더의 제목을 새 제목으로 교체
        def replace_title(match):
            return f'<span class="category-title-text">{new_title}</span>'
        template_header = re.sub(
            r'<span class="category-title-text">.*?</span>',
            replace_title,
            template_header,
            flags=re.DOTALL
        )
        
        # 목록 링크도 폴더명에 맞게 수정
        list_link_pattern = r'href="../../CBT-list/[^"]*-list\.html"'
        new_list_link = f'href="../../CBT-list/{folder_name}-list.html"'
        template_header = re.sub(list_link_pattern, new_list_link, template_header)
        
        # 새로운 내용 조합: 기준 파일의 헤더(스타일, 버튼 포함) + 대상 파일의 문제 내용 + 기준 파일의 푸터
        new_content = template_header + problem_content + template_footer
        
        # 보기 번호 수정: 문제 내용에서 05 -> ⑤ (5번째 보기)
        # 보기 번호가 05로 표시된 경우를 ⑤로 변경
        # 정규식으로 <li> 태그 내용에서 "05"를 "⑤"로 변경 (날짜 등 다른 "05"는 제외하기 위해 <li> 내부만)
        new_content = re.sub(r'(<li[^>]*>)(.*?)05(.*?)(</li>)', r'\1\2⑤\3\4', new_content)
        
        # 변경사항 확인
        if new_content == original_target:
            return False  # 변경사항 없음
        
        # 파일 저장 (dry_run이 False일 때만)
        if not dry_run:
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"❌ {target_file.name} 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    print("=" * 60)
    print("CBT 폴더 전체 HTML 파일 구조 적용 스크립트")
    print("제목, 문제, 보기, 해설, 이미지 링크는 파일에 맞게 변경")
    print("스타일, 버튼은 기준 파일과 동일하게 유지")
    print("=" * 60)
    print()
    
    # 기준 파일 확인
    if not TEMPLATE_FILE.exists():
        print(f"❌ 기준 파일을 찾을 수 없습니다: {TEMPLATE_FILE}")
        return
    
    # CBT 폴더의 모든 HTML 파일 찾기 (재귀적으로)
    cbt_folder = Path("CBT")
    if not cbt_folder.exists():
        print("❌ CBT 폴더를 찾을 수 없습니다.")
        return
    
    html_files = list(cbt_folder.rglob("*.html"))
    
    # 기준 파일과 백업 폴더 제외
    html_files = [f for f in html_files if f != TEMPLATE_FILE and '백업' not in str(f)]
    
    print(f"📁 총 {len(html_files)}개의 HTML 파일을 찾았습니다.")
    print(f"📄 기준 파일: {TEMPLATE_FILE}")
    print()
    
    # Dry run 먼저 실행 (처음 10개만 테스트)
    print("=" * 60)
    print("1단계: DRY RUN (처음 10개 파일 테스트)")
    print("=" * 60)
    modified_count = 0
    for file_path in html_files[:10]:
        if apply_exact_structure(TEMPLATE_FILE, file_path, dry_run=True):
            print(f"✅ {file_path.relative_to(cbt_folder)} - 수정 필요")
            modified_count += 1
        else:
            print(f"⏭️  {file_path.relative_to(cbt_folder)} - 변경사항 없음 또는 스킵")
    
    print()
    print(f"📊 DRY RUN 결과 (처음 10개): {modified_count}/10개 파일 수정 필요")
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
            if apply_exact_structure(TEMPLATE_FILE, file_path, dry_run=False):
                print(f"✅ [{i}/{len(html_files)}] {file_path.relative_to(cbt_folder)} - 수정 완료")
                success_count += 1
            else:
                skip_count += 1
                if i % 100 == 0 or i <= 10:
                    print(f"⏭️  [{i}/{len(html_files)}] {file_path.relative_to(cbt_folder)} - 변경사항 없음 또는 스킵")
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
