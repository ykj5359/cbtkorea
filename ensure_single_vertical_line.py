#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ERP-인사-2급-실무 폴더의 HTML 파일에서
세로선이 한 줄만 나오도록 CSS 수정
"""

import sys
import re
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 정확한 세로선 CSS (하나만 있도록)
CORRECT_VERTICAL_LINE_CSS = """    /* 좌우 구분선 - 얇은 연결된 선 */
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


def replace_vertical_line_css(content):
    """세로선 CSS를 정확한 하나의 버전으로 교체"""
    # 기존 세로선 관련 CSS 찾기 (좌우 구분선 주석부터 문제 간 간격까지)
    pattern = r'/\* 좌우 구분선[^*]*\*/.*?\.exam-box\.exam-right\s*\{[^}]*padding-left:[^}]*\}'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # 기존 CSS를 정확한 버전으로 교체
        start = match.start()
        end = match.end()
        new_content = content[:start] + CORRECT_VERTICAL_LINE_CSS + content[end:]
        return new_content, True
    
    # 패턴을 찾을 수 없는 경우, /* 틀린 경우 일반 폰트 */ 다음에 추가
    pattern2 = r'(/\* 틀린 경우 일반 폰트 \*/[^}]*\}[^}]*\})'
    match2 = re.search(pattern2, content, re.DOTALL)
    
    if match2:
        insert_pos = match2.end()
        new_content = content[:insert_pos] + '\n    \n' + CORRECT_VERTICAL_LINE_CSS + content[insert_pos:]
        return new_content, True
    
    return content, False


def process_file(file_path, dry_run=False):
    """단일 파일 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_content, modified = replace_vertical_line_css(content)
        
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
    print("ERP-인사-2급-실무 폴더 세로선 CSS 정리")
    print("세로선이 한 줄만 나오도록 수정")
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
