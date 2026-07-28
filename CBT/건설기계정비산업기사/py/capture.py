import os
import asyncio
from playwright.async_api import async_playwright

async def capture_html_questions(file_path):
    async with async_playwright() as p:
        # 고화질 영상 소스를 위해 브라우저 설정
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1200, 'height': 800})
        page = await context.new_page()

        # HTML 파일 경로 확인
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            print(f"에러: {file_path} 파일을 찾을 수 없습니다.")
            return

        # 로컬 파일 열기
        await page.goto(f"file:///{abs_path}")
        # 페이지 로딩 대기
        await page.wait_for_timeout(2000)

        # 킨즈/CBT 형식의 문제 박스 찾기
        questions = await page.query_selector_all(".exam-box")
        
        # 저장할 폴더 생성
        folder_name = "captured_images"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        print(f"작업 시작: {len(questions)}개의 문제를 찾았습니다.")

        for i, question in enumerate(questions):
            # 파일명: question_01.png, question_02.png ...
            output_path = f"{folder_name}/question_{str(i+1).zfill(2)}.png"
            
            # 문제 영역만 캡처
            await question.screenshot(path=output_path)
            print(f"{i+1}번 완료: {output_path}")

        await browser.close()
        print(f"\n모든 작업이 끝났습니다! '{folder_name}' 폴더를 확인하세요.")

if __name__ == "__main__":
    # 캡처할 HTML 파일 이름을 여기에 적으세요 (파일이 같은 폴더에 있어야 함)
    target_file = "gw20050306.html" 
    asyncio.run(capture_html_questions(target_file))