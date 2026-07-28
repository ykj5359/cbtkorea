#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ERP-인사-2급-실무 폴더의 HTML 파일에
가운데 세로선 CSS 추가
"""

import sys
import re
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 추가할 세로선 CSS (기준: ERP-회계-2급-이론)
VERTICAL_LINE_CSS = """    /* 좌우 구분선 - 얇은 연결된 선 */
    .row.text-dark {
        position: relative;
    }
    .row.text-dark::after {
        content: '';
        position: absolute;
        top: 0;
        right: 50%;
        bottom: 0;
        width: 1px;
        background-color: #e5e7eb;
        z-index: 1;
    }
    
    /* 작은 화면에서 가운데 줄 숨김 (2열이 1열로 바뀔 때) */
    @media (max-width: 767.98px) {
        .row.text-dark::after {
            display: none !important;
        }
        .exam-box.exam-left {
            padding-right: 0 !important;
        }
        .exam-box.exam-right {
            padding-left: 0 !important;
        }
    }
    .exam-box.exam-left {
        border-right: none !important;
        padding-right: 20px !important;
    }
    .exam-box.exam-right {
        padding-left: 20px !important;
    }
"""


def has_vertical_line_css(content):
    """세로선 CSS가 이미 있는지 확인"""
    return '.row.text-dark::after' in content and 'right: 50%' in content


def add_vertical_line_css(content):
    """세로선 CSS 추가"""
    # 이미 있으면 추가하지 않음
    if has_vertical_line_css(content):
        return content, False
    
    # .question-choice li.wrong 스타일 다음에 추가
    # 또는 /* 문제 간 간격 */ 전에 추가
    pattern = r'(/\* 문제 간 간격 \*/)'
    match = re.search(pattern, content)
    
    if match:
        # /* 문제 간 간격 */ 전에 추가
        insert_pos = match.start()
        new_content = content[:insert_pos] + VERTICAL_LINE_CSS + '\n    ' + content[insert_pos:]
        return new_content, True
    
    # /* 틀린 경우 일반 폰트 */ 다음에 추가
    pattern2 = r'(/\* 틀린 경우 일반 폰트 \*/[^}]*\}[^}]*\})'
    match2 = re.search(pattern2, content, re.DOTALL)
    
    if match2:
        insert_pos = match2.end()
        new_content = content[:insert_pos] + '\n    \n' + VERTICAL_LINE_CSS + content[insert_pos:]
        return new_content, True
    
    # 스타일 태그 내부 끝부분에 추가
    pattern3 = r'(</style>)'
    match3 = re.search(pattern3, content)
    
    if match3:
        insert_pos = match3.start()
        new_content = content[:insert_pos] + '    \n' + VERTICAL_LINE_CSS + content[insert_pos:]
        return new_content, True
    
    return content, False


def process_file(file_path, dry_run=False):
    """단일 파일 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_content, modified = add_vertical_line_css(content)
        
        if not modified:
            return False  # 변경사항 없음 (이미 있거나 추가 실패)
        
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
    print("ERP-인사-2급-실무 폴더 가운데 세로선 CSS 추가")
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
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        has_css = has_vertical_line_css(content)
        
        if process_file(file_path, dry_run=True):
            print(f"✅ {file_path.name} - 세로선 CSS 추가 필요")
            modified_count += 1
        else:
            status = "이미 있음" if has_css else "추가 실패"
            print(f"⏭️  {file_path.name} - {status}")
    
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
                print(f"✅ [{i}/{len(html_files)}] {file_path.name} - 세로선 CSS 추가 완료")
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
