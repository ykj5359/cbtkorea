@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   CBT 기출문제 - 운영자 데일리 글 생성
echo ============================================
python gen_community_post.py
echo.
echo * 완료. (별도 웹호스팅에 업로드하는 구조라면
echo   cbt-community-feed.js 를 다시 업로드하세요)
echo.
timeout /t 4 >nul
