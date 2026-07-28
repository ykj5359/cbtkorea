#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
문제 하단 버튼을 기준 파일 형식으로 변경
"정답, 공유, 체크, 작성, 해설1" -> "정답, 체크, 해설"
기준 파일: CBT/건설안전기사/nj20030316 - 복사본.html
"""

import re
import sys
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def fix_exam_buttons(content):
    """문제 하단 버튼을 기준 파일 형식으로 변경"""
    # 기준 파일의 버튼 구조: 정답, 체크, 해설
    standard_buttons = '<button class="correct-number btn btn-outline-secondary" type="button">정답</button><button class="chk-question btn btn-outline-secondary" type="button">체크</button><button class="show-comment btn btn-outline-secondary" type="button">해설</button>'
    
    # 패턴: <div class="col-12 exam-buttons text-center">...버튼들...</div></div>
    # 다양한 버튼 조합을 처리
    pattern = r'(<div class="col-12 exam-buttons[^"]*">)(.*?)(</div></div>)'
    
    def replace_buttons(match):
        opening_div = match.group(1)
        buttons_html = match.group(2)
        closing_divs = match.group(3)
        
        # 버튼들을 기준 형식으로 교체
        return opening_div + standard_buttons + closing_divs
    
    new_content = re.sub(pattern, replace_buttons, content, flags=re.DOTALL)
    
    return new_content


def process_file(file_path, dry_run=False):
    """단일 파일 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_content = fix_exam_buttons(content)
        
        if new_content == original_content:
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
    print("건축기사 폴더 문제 하단 버튼 수정 스크립트")
    print("'정답, 공유, 체크, 작성, 해설1' -> '정답, 체크, 해설'")
    print("=" * 60)
    print()
    
    folder = Path("CBT/건축기사")
    if not folder.exists():
        print("❌ CBT/건축기사 폴더를 찾을 수 없습니다.")
        return
    
    html_files = list(folder.glob("*.html"))
    
    print(f"📁 총 {len(html_files)}개의 HTML 파일을 찾았습니다.")
    print()
    
    # Dry run 먼저 실행 (처음 3개만 테스트)
    print("=" * 60)
    print("1단계: DRY RUN (처음 3개 파일 테스트)")
    print("=" * 60)
    
    modified_count = 0
    for file_path in html_files[:3]:
        if process_file(file_path, dry_run=True):
            print(f"✅ {file_path.name} - 수정 필요")
            modified_count += 1
        else:
            print(f"⏭️  {file_path.name} - 변경사항 없음")
    
    print()
    print(f"📊 DRY RUN 결과 (처음 3개): {modified_count}/3개 파일 수정 필요")
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
                print(f"✅ [{i}/{len(html_files)}] {file_path.name} - 수정 완료")
                success_count += 1
            else:
                skip_count += 1
                if i % 10 == 0 or i <= 3:
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
