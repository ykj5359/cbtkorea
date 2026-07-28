#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
마지막 문제에 "정답, 체크, 해설" 버튼이 없는 파일을 찾아서 추가
"""

import re
import sys
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 기준 버튼 구조
STANDARD_BUTTONS = '<button class="correct-number btn btn-outline-secondary" type="button">정답</button><button class="chk-question btn btn-outline-secondary" type="button">체크</button><button class="show-comment btn btn-outline-secondary" type="button">해설</button>'
BUTTON_HTML = f'<div class="row"><div class="col-12 exam-buttons text-center">{STANDARD_BUTTONS}</div></div>'


def extract_problem_content(content):
    """문제 내용 부분 추출"""
    exams_start = content.find('<div class="exams')
    if exams_start == -1:
        exams_start = content.find('<div class="row">')
        if exams_start != -1:
            temp_start = content.find('<div class="exams', exams_start)
            if temp_start != -1:
                exams_start = content.rfind('<div class="row">', exams_start, temp_start)
    
    if exams_start == -1:
        return None, None, None
    
    footer_start = content.find('<!-- 하단 시작', exams_start)
    if footer_start == -1:
        footer_start = content.find('<footer', exams_start)
    if footer_start == -1:
        footer_start = content.rfind('</div></div></div></div></div>', exams_start)
        if footer_start != -1:
            footer_start += len('</div></div></div></div></div>')
    
    if footer_start == -1:
        return None, None, None
    
    problem_content = content[exams_start:footer_start]
    return problem_content, exams_start, footer_start


def check_and_add_button(content):
    """마지막 문제에 버튼이 있는지 확인하고 없으면 추가"""
    problem_content, problem_start, problem_end = extract_problem_content(content)
    
    if problem_content is None:
        return content, False
    
    # 마지막 exam-box 찾기
    exam_box_pattern = r'<div[^>]*class="[^"]*exam-box[^"]*"[^>]*>'
    exam_boxes = list(re.finditer(exam_box_pattern, problem_content))
    
    if not exam_boxes:
        return content, False
    
    # 마지막 문제 영역 확인
    last_exam_start_in_content = exam_boxes[-1].start()
    last_exam_content = problem_content[last_exam_start_in_content:]
    
    # 마지막 문제에 exam-buttons가 있는지 확인
    if 'exam-buttons' in last_exam_content:
        return content, False  # 이미 버튼이 있음
    
    # 마지막 문제의 끝 부분 찾기 (reply div가 끝나는 부분 후)
    # </div></div></div></div> 패턴 찾기 (reply div의 끝)
    # 마지막 문제 영역의 끝 부분 찾기
    # </div></div></div></div> 패턴을 뒤에서 찾기
    div_end_pattern = r'</div></div></div></div>'
    div_end_matches = list(re.finditer(div_end_pattern, last_exam_content))
    
    if not div_end_matches:
        return content, False
    
    # 마지막 문제 영역의 끝 (문제 영역 전체를 닫는 </div></div></div></div></div> 전의 </div></div></div></div>)
    # 마지막에서 두 번째 </div></div></div></div> 위치 찾기
    if len(div_end_matches) >= 2:
        insert_pos_in_last_exam = div_end_matches[-2].end()
    else:
        # 하나만 있으면 그것을 사용
        insert_pos_in_last_exam = div_end_matches[-1].start()
    
    # 전체 파일에서의 위치 계산
    insert_position = problem_start + last_exam_start_in_content + insert_pos_in_last_exam
    
    # 버튼 추가
    new_content = content[:insert_position] + BUTTON_HTML + content[insert_position:]
    return new_content, True


def process_file(file_path, dry_run=False):
    """단일 파일 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_content, added = check_and_add_button(content)
        
        if not added:
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
    print("마지막 문제에 버튼이 없는 파일 찾아서 추가")
    print("=" * 60)
    print()
    
    cbt_folder = Path("CBT")
    if not cbt_folder.exists():
        print("❌ CBT 폴더를 찾을 수 없습니다.")
        return
    
    html_files = list(cbt_folder.rglob("*.html"))
    
    # 백업 폴더 제외
    html_files = [f for f in html_files if '백업' not in str(f)]
    
    print(f"📁 총 {len(html_files)}개의 HTML 파일을 찾았습니다.")
    print()
    
    # Dry run 먼저 실행 (처음 10개만 테스트)
    print("=" * 60)
    print("1단계: DRY RUN (처음 10개 파일 테스트)")
    print("=" * 60)
    
    modified_count = 0
    for file_path in html_files[:10]:
        if process_file(file_path, dry_run=True):
            print(f"✅ {file_path.relative_to(cbt_folder)} - 버튼 추가 필요")
            modified_count += 1
        else:
            print(f"⏭️  {file_path.relative_to(cbt_folder)} - 이미 버튼이 있음")
    
    print()
    print(f"📊 DRY RUN 결과 (처음 10개): {modified_count}/10개 파일에 버튼 추가 필요")
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
                print(f"✅ [{i}/{len(html_files)}] {file_path.relative_to(cbt_folder)} - 버튼 추가 완료")
                success_count += 1
            else:
                skip_count += 1
                if i % 100 == 0 or i <= 10:
                    print(f"⏭️  [{i}/{len(html_files)}] {file_path.relative_to(cbt_folder)} - 이미 버튼이 있음")
        except Exception as e:
            error_count += 1
            print(f"❌ [{i}/{len(html_files)}] {file_path.relative_to(cbt_folder)} - 오류: {e}")
    
    print()
    print("=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"📊 총 파일 수: {len(html_files)}개")
    print(f"✅ 버튼 추가 완료: {success_count}개")
    print(f"⏭️  이미 버튼 있음: {skip_count}개")
    print(f"❌ 오류: {error_count}개")


if __name__ == "__main__":
    main()
