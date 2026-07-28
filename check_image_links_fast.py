#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CBT 폴더의 모든 HTML 파일에서 GIF 이미지 링크 확인
이미지 파일이 실제로 존재하는지 체크
결과를 파일로 저장
"""

import sys
import re
from pathlib import Path
from urllib.parse import unquote

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def find_image_links(content, file_path):
    """HTML 내용에서 이미지 링크 찾기"""
    # img 태그의 src 속성 찾기
    pattern = r'<img[^>]+src=["\']([^"\']+\.gif[^"\']*)["\']'
    matches = re.finditer(pattern, content, re.IGNORECASE)
    
    image_links = []
    for match in matches:
        src = match.group(1)
        # HTML 엔티티 디코딩
        src = unquote(src)
        image_links.append(src)
    
    return image_links


def check_image_exists(image_path, html_file_path):
    """이미지 파일이 존재하는지 확인"""
    html_dir = html_file_path.parent
    
    # 절대 URL인 경우 (http://, https://) - 스킵
    if image_path.startswith(('http://', 'https://')):
        return True, "외부 URL"
    
    # 상대 경로 처리
    if image_path.startswith('/'):
        # 루트부터 시작하는 경로는 프로젝트 루트 기준
        project_root = Path("CBT").parent
        full_path = project_root / image_path.lstrip('/')
    else:
        # 상대 경로는 HTML 파일 위치 기준
        full_path = (html_dir / image_path).resolve()
    
    # 파일 존재 확인
    if full_path.exists() and full_path.is_file():
        return True, "존재"
    else:
        return False, str(full_path)


def process_file(file_path):
    """단일 파일 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        image_links = find_image_links(content, file_path)
        
        broken_links = []
        total_links = len(image_links)
        
        for img_src in image_links:
            exists, status = check_image_exists(img_src, file_path)
            if not exists:
                broken_links.append((img_src, status))
        
        return total_links, broken_links
        
    except Exception as e:
        return None, f"오류: {e}"


def main():
    """메인 함수"""
    print("=" * 60)
    print("HTML 파일 GIF 이미지 링크 확인")
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
    print("이미지 링크 확인 중...")
    print("(진행 상황은 100개마다 표시됩니다)")
    print()
    
    total_files = len(html_files)
    files_with_images = 0
    files_with_broken_links = 0
    total_image_links = 0
    total_broken_links = 0
    
    broken_files = []
    output_lines = []
    
    for i, file_path in enumerate(html_files, 1):
        if i % 100 == 0:
            print(f"진행 중... {i}/{total_files} ({i*100//total_files}%)")
        
        result = process_file(file_path)
        
        if isinstance(result[1], str):  # 오류
            continue
        
        total_links, broken_links = result
        
        if total_links > 0:
            files_with_images += 1
            total_image_links += total_links
            total_broken_links += len(broken_links)
            
            if broken_links:
                files_with_broken_links += 1
                rel_path = str(file_path.relative_to(cbt_folder))
                broken_files.append((rel_path, broken_links))
                output_lines.append(f"\n📄 {rel_path}")
                for img_src, status in broken_links:
                    output_lines.append(f"   ❌ {img_src}")
                    output_lines.append(f"      {status}")
    
    # 결과 출력
    print()
    print("=" * 60)
    print("확인 완료!")
    print("=" * 60)
    print(f"📊 총 HTML 파일 수: {total_files}개")
    print(f"📷 이미지가 있는 파일: {files_with_images}개")
    print(f"🔗 총 이미지 링크 수: {total_image_links}개")
    print(f"❌ 깨진 링크가 있는 파일: {files_with_broken_links}개")
    print(f"🔴 총 깨진 링크 수: {total_broken_links}개")
    print()
    
    # 결과를 파일로 저장
    output_file = Path("image_links_check_result.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("HTML 파일 GIF 이미지 링크 확인 결과\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"📊 총 HTML 파일 수: {total_files}개\n")
        f.write(f"📷 이미지가 있는 파일: {files_with_images}개\n")
        f.write(f"🔗 총 이미지 링크 수: {total_image_links}개\n")
        f.write(f"❌ 깨진 링크가 있는 파일: {files_with_broken_links}개\n")
        f.write(f"🔴 총 깨진 링크 수: {total_broken_links}개\n\n")
        
        if broken_files:
            f.write("=" * 60 + "\n")
            f.write("깨진 이미지 링크가 있는 파일:\n")
            f.write("=" * 60 + "\n")
            f.write("\n".join(output_lines))
        else:
            f.write("✅ 모든 이미지 링크가 정상적으로 연결되어 있습니다!\n")
    
    print(f"📄 상세 결과는 '{output_file}' 파일에 저장되었습니다.")
    
    if broken_files:
        print()
        print(f"⚠️  {len(broken_files)}개 파일에 깨진 이미지 링크가 있습니다.")
        print("   상세 내용은 위 파일을 확인하세요.")
    else:
        print()
        print("✅ 모든 이미지 링크가 정상적으로 연결되어 있습니다!")


if __name__ == "__main__":
    main()
